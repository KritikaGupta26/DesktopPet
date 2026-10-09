"""Extract approved whole-body scenes; preserve scale across each source sheet."""
from pathlib import Path
import json
import io
import os
from PIL import Image, ImageDraw
import numpy as np
from scipy.ndimage import label, find_objects

ROOT = Path(__file__).resolve().parents[1]


def save_atomic(image,path,**options):
    buffer=io.BytesIO()
    image.save(buffer,format="GIF" if path.suffix==".gif" else "PNG",**options)
    temporary=path.with_suffix(path.suffix+".tmp")
    with temporary.open("wb") as target:
        target.write(buffer.getvalue());target.flush();os.fsync(target.fileno())
    temporary.replace(path)


def export_scenes():
    config = json.loads((ROOT/'artwork/v32/export_config.json').read_text())
    for key, metadata in config.items():
        with Image.open(ROOT/metadata['source']) as opened:
            sheet = opened.convert('RGBA')
        columns, rows = metadata['grid']
        frames = []
        for index in range(metadata['frames']):
            col, row = index % columns, index // columns
            left,right=round(col*sheet.width/columns),round((col+1)*sheet.width/columns)
            top,bottom=round(row*sheet.height/rows),round((row+1)*sheet.height/rows)
            if rows==2:
                # Generators leave unequal gutters. Locate the gap between the
                # two whole pandas, instead of cutting at nominal half-height.
                column=np.array(sheet)[:,left:right,3]>=128
                labels,_=label(column)
                bodies=[]
                for component, area in enumerate(find_objects(labels),1):
                    if area is not None:
                        bodies.append((int((labels[area]==component).sum()),area))
                bodies=sorted(bodies,key=lambda item:item[0],reverse=True)[:2]
                if len(bodies)==2:
                    upper,lower=sorted((item[1] for item in bodies),key=lambda a:a[0].start)
                    if upper[0].stop<=lower[0].start:
                        split=(upper[0].stop+lower[0].start)//2
                        top,bottom=(0,split) if row==0 else (split,sheet.height)
            rect=(left,top,right,bottom)
            frame = sheet.crop(rect)
            if key == 'spooky' and index >= 4:
                with Image.open(ROOT/'artwork/v32/spooky_carve_source.png') as source:
                    source = source.convert('RGBA')
                n = index-4
                frame = source.crop((round(n*source.width/4),0,round((n+1)*source.width/4),source.height))
                ratio = sheet.width/source.width
                frame = frame.resize((round(frame.width*ratio),round(frame.height*ratio)),Image.Resampling.LANCZOS)
            # Cell boundaries can include a thin toe from the preceding row.
            pixels = np.array(frame)
            mask = pixels[:,:,3]>=128
            labels, count = label(mask)
            sizes=np.bincount(labels.ravel());sizes[0]=0
            largest=int(sizes.max())
            for component, area in enumerate(find_objects(labels),1):
                if area is None:
                    continue
                ys,xs=area
                size=int((labels[area]==component).sum())
                touches_row = ys.start<5 or ys.stop>frame.height-5
                touches_column=xs.start<5 or xs.stop>frame.width-5
                if ((touches_row and ys.stop-ys.start<12 and size<700)
                        or (touches_column and size<largest*.20)):
                    pixels[labels==component,3]=0
            pixels[pixels[:,:,3]<128,3]=0
            frame=Image.fromarray(pixels)
            box = frame.getchannel('A').point(lambda a:255 if a>=128 else 0).getbbox()
            if not box:
                raise ValueError(f'Empty pose: {key}:{index}')
            frames.append(frame.crop(box))
        # Shared scale: crouching/sitting never magnified to standing height.
        scale = min(450/max(f.height for f in frames),464/max(f.width for f in frames))
        previews = []
        for index, frame in enumerate(frames):
            size = (round(frame.width*scale),round(frame.height*scale))
            sprite = frame.resize(size,Image.Resampling.LANCZOS)
            out = Image.new('RGBA',(512,512))
            out.alpha_composite(sprite,((512-size[0])//2,489-size[1]))
            save_atomic(out,ROOT/f'assets/scene_{key}_{index}.png',optimize=True)
            thumb = out.resize((180,180),Image.Resampling.LANCZOS)
            preview = Image.new('RGB',(180,204),'#f4eadd')
            preview.paste(thumb,(0,24),thumb)
            ImageDraw.Draw(preview).text((5,5),f'{key} {index}',fill='#332c27')
            previews.append(preview)
        contact = Image.new('RGB',(720,408),'#f4eadd')
        for i, preview in enumerate(previews):
            contact.paste(preview,((i%4)*180,(i//4)*204))
        save_atomic(contact,ROOT/f'artwork/v32/{key}_audit.png')
        ordered = [previews[i] for i,_ in metadata['timeline']]
        save_atomic(ordered[0],ROOT/f'artwork/v32/{key}_playback.gif',save_all=True,
                        append_images=ordered[1:],duration=[round(s*1000) for _,s in metadata['timeline']],loop=0)
    (ROOT/'assets/scene_manifest.json').write_text(json.dumps(config,indent=2))


if __name__ == '__main__':
    export_scenes()
