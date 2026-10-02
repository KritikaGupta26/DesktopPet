from PIL import Image,ImageOps,ImageFilter
from pathlib import Path
import json,shutil
root=Path(__file__).resolve().parents[1]
source=root/'artwork/walk_v25_source.png'
(root/'artwork/v24_walk').mkdir(parents=True,exist_ok=True)
for p in (root/'assets').glob('pack_walk*.png'):
 if not (root/'artwork/v24_walk'/p.name).exists():shutil.copy2(p,root/'artwork/v24_walk'/p.name)
sheet=Image.open(source).convert('RGBA');frames=[];rects=[]
for i in range(8):
 col=i%4;row=i//4;rect=(round(col*sheet.width/4),round(row*sheet.height/2),round((col+1)*sheet.width/4),round((row+1)*sheet.height/2));rects.append(list(rect))
 frame=sheet.crop(rect);alpha=frame.getchannel('A');inner=alpha.point(lambda a:255 if a>=128 else 0).filter(ImageFilter.MinFilter(7));pix=frame.load();safe=inner.load()
 for y in range(frame.height):
  for x in range(frame.width):
   r,g,b,a=pix[x,y]
   if safe[x,y]==0 and max(r,g,b)-min(r,g,b)>170 and a>0:pix[x,y]=(r,g,b,0)
 box=frame.getchannel('A').point(lambda a:255 if a>=128 else 0).getbbox();assert box
 frames.append(frame.crop(box))
scale=min(450/max(im.height for im in frames),460/max(im.width for im in frames))
for i,im in enumerate(frames):
 im=im.resize((round(im.width*scale),round(im.height*scale)),Image.Resampling.LANCZOS);out=Image.new('RGBA',(512,512));out.alpha_composite(im,((512-im.width)//2,489-im.height));out.save(root/f'assets/pack_walk_{i}.png',optimize=True);ImageOps.mirror(out).save(root/f'assets/pack_walk_left_{i}.png',optimize=True)
manifest=json.loads((root/'assets/sprite_collection_manifest.json').read_text());manifest['walk'].update(generated_source='artwork/walk_v25_source.png',previous_frames='artwork/v24_walk',crop_rectangles=rects,shared_scale=scale,selected_playback_frames=[0,1,2,4,5,6]);(root/'assets/sprite_collection_manifest.json').write_text(json.dumps(manifest,indent=2))
for direction in ['right','left']:
 seq=[]
 for i in [0,1,2,4,5,6]:
  im=Image.open(root/f'assets/pack_walk{"_left" if direction=="left" else ""}_{i}.png').convert('RGBA');im.thumbnail((180,180),Image.Resampling.LANCZOS);bg=Image.new('RGB',(220,220),'#f4eadd');bg.paste(im,(20,20),im);seq.append(bg)
 seq[0].save(root/f'artwork/walk_v25_{direction}.gif',save_all=True,append_images=seq[1:],duration=240,loop=0)
print('Prepared 8 complete source poses, 6 selected walk phases, mirrored directions, preserved previous frames.')
