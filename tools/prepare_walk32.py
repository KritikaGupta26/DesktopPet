"""Package eight separately reviewed whole-body low-stride poses."""
from pathlib import Path
import json
import io
import os
from PIL import Image, ImageOps, ImageDraw
import numpy as np
from scipy.ndimage import label

ROOT=Path(__file__).resolve().parents[1]


def save_atomic(image,path,**options):
    buffer=io.BytesIO()
    image.save(buffer,format="GIF" if path.suffix==".gif" else "PNG",**options)
    temporary=path.with_suffix(path.suffix+".tmp")
    with temporary.open("wb") as target:
        target.write(buffer.getvalue());target.flush();os.fsync(target.fileno())
    temporary.replace(path)


def main():
    previews=[]
    for i in range(8):
        source=ROOT/f'artwork/v32/walk_{i}_source.png'
        im=Image.open(source).convert('RGBA')
        pixels=np.array(im)
        labels,count=label(pixels[:,:,3]>=128)
        sizes=np.bincount(labels.ravel());sizes[0]=0
        main_component=int(sizes.argmax())
        # Whole-body single poses must never bring neighbouring cell scraps.
        pixels[labels!=main_component,3]=0
        im=Image.fromarray(pixels)
        bbox=im.getchannel('A').getbbox()
        im=im.crop(bbox)
        scale=min(450/im.height,456/im.width)
        head=im.getchannel('A').crop((0,0,im.width,round(im.height*.49))).getbbox()
        head_x=(head[0]+head[2])/2
        sprite=im.resize((round(im.width*scale),round(im.height*scale)),Image.Resampling.LANCZOS)
        x=round(276-head_x*scale)
        x=max(24,min(x,488-sprite.width))
        out=Image.new('RGBA',(512,512));out.alpha_composite(sprite,(x,489-sprite.height))
        save_atomic(out,ROOT/f'assets/pack_walk_{i}.png',optimize=True)
        save_atomic(ImageOps.mirror(out),ROOT/f'assets/pack_walk_left_{i}.png',optimize=True)
        thumb=out.resize((180,180),Image.Resampling.LANCZOS)
        bg=Image.new('RGB',(180,204),'#f4eadd');bg.paste(thumb,(0,24),thumb)
        ImageDraw.Draw(bg).text((4,5),f'walk {i}',fill='#332c27');previews.append(bg)
    contact=Image.new('RGB',(720,408),'#f4eadd')
    for i,bg in enumerate(previews):contact.paste(bg,((i%4)*180,(i//4)*204))
    save_atomic(contact,ROOT/'artwork/v32/walk_audit.png')
    for direction in ('right','left'):
        poses=[]
        for i in range(8):
            im=Image.open(ROOT/f'assets/pack_walk{"_left" if direction=="left" else ""}_{i}.png').resize((180,180))
            bg=Image.new('RGB',(180,184),'#f4eadd');bg.paste(im,(0,4),im);poses.append(bg)
        save_atomic(poses[0],ROOT/f'artwork/v32/walk_{direction}.gif',save_all=True,append_images=poses[1:],duration=180,loop=0)
    path=ROOT/'assets/sprite_collection_manifest.json';manifest=json.loads(path.read_text())
    manifest['walk'].update(generated_source='artwork/v32/walk_0_source.png',
        generated_sources=[f'artwork/v32/walk_{i}_source.png' for i in range(8)],
        selected_playback_frames=list(range(8)),head_anchor_x=276,ground_anchor_y=489,
        pose_phases=['contact A','down A','passing A','up A','contact B','down B','passing B','up B'])
    path.write_text(json.dumps(manifest,indent=2))


if __name__=='__main__':main()
