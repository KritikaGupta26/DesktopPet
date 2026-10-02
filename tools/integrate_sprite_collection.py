"""Prepare all supplied sprite rows with shared per-action scale and clean alpha."""
from pathlib import Path
import json, sys
from zipfile import ZipFile
from io import BytesIO
import numpy as np
from PIL import Image, ImageOps
from scipy.ndimage import label, binary_dilation, find_objects

SHEETS = [
 ('01_water_offer',4,2,['water_offer']),('02_walk',4,2,['walk']),('03_run',4,2,['run']),('04_jump',4,2,['jump']),
 ('05_interactions',4,4,['wave','petting','cursor_follow','cursor_avoid']),
 ('06_expressions',6,4,['happy_idle','ear_rub','bored_shuffle','sad']),
 ('07_reminders',6,4,['alternate_offer','drink_water','watch','alternate_hoop']),
 ('08_activities',6,4,['kung_fu','bamboo_hang','yawn_stretch','sleep']),
 ('09_hula_hoop',4,2,['hula_hoop']),
 ('10_bamboo_and_log',4,4,['eat_bamboo','carry_bamboo','sit_on_log','balance_on_log']),
 ('11_games',4,4,['peekaboo','chase_ball','catch_ball','victory']),
 ('12_manners',4,4,['bow','greeting','clap','blow_kiss']),
 ('13_floor_poses',4,4,['sploot','side_roll','belly_scratch','lazy_stretch']),
 ('14_silly_play',4,4,['dance','wiggle','sneeze','hiccup']),
 ('15_rest_and_groom',4,4,['sit_down','wash_face','wake_up','snore_sleep']),
 ('16_fetch',4,2,['fetch']),('17_somersault',4,2,['forward_roll'])]

LOOPS={'walk','run','happy_idle','ear_rub','bored_shuffle','sad','alternate_hoop','sleep','hula_hoop','eat_bamboo','balance_on_log','chase_ball','dance','wiggle','belly_scratch','snore_sleep'}
SLOW={'sleep','snore_sleep','bored_shuffle','sit_on_log','balance_on_log'}

def prepare(archive, assets, previews):
 assets.mkdir(parents=True,exist_ok=True);previews.mkdir(parents=True,exist_ok=True)
 manifest={};z=ZipFile(archive)
 for sheet,cols,rows,actions in SHEETS:
  image=Image.open(BytesIO(z.read(f'sprites/{sheet}.png'))).convert('RGBA')
  sheet_array=np.array(image);sheet_labels,n=label(sheet_array[:,:,3]>=64)
  sheet_counts=np.bincount(sheet_labels.ravel());sheet_counts[0]=0
  sheet_boxes=find_objects(sheet_labels)
  for row,key in enumerate(actions):
   count=cols*rows if len(actions)==1 else cols;frames=[];crop_records=[];heads=[]
   for i in range(count):
    r=i//cols if len(actions)==1 else row;c=i%cols
    rect=(round(c*image.width/cols),round(r*image.height/rows),round((c+1)*image.width/cols),round((r+1)*image.height/rows))
    # The artwork crosses nominal grid lines. Isolate complete connected
    # characters on the full sheet before cropping, never cut at a cell edge.
    arr=sheet_array.copy();labs=sheet_labels;counts=sheet_counts
    candidates=[]
    for component in range(1,len(counts)):
     if counts[component]<1500:continue
     box=sheet_boxes[component-1]
     center=((box[1].start+box[1].stop)/2,(box[0].start+box[0].stop)/2)
     if int(center[0]*cols/image.width)==c and int(center[1]*rows/image.height)==r:
      candidates.append(component)
    if not candidates:raise ValueError(f'No complete character {sheet} {i}')
    main=max(candidates,key=lambda component:counts[component])
    retained=[component for component in candidates if counts[component]>=max(64,counts[main]*.008)]
    keep=binary_dilation(np.isin(labs,retained),iterations=2)
    arr[:,:,3]=np.where(keep,arr[:,:,3],0)
    crop=Image.fromarray(arr);crop=crop.crop(crop.getchannel('A').getbbox())
    if key in ('wave','greeting') and i==2:crop=ImageOps.mirror(crop)
    arr=np.array(crop);cream=(arr[:,:,0]>160)&(arr[:,:,1]>140)&(arr[:,:,2]>110)&(arr[:,:,3]>128)
    cream[int(crop.height*.62):]=False
    labs,n=label(cream);counts=np.bincount(labs.ravel());counts[0]=0
    if counts.max():
     ys,xs=np.where(labs==int(counts.argmax()));heads.append(int(xs.max()-xs.min()+1))
    frames.append(crop);crop_records.append(rect)
   desired=250/max(1,float(np.median(heads))) if heads else 1
   scale=min(desired,472/max(f.width for f in frames),472/max(f.height for f in frames))
   prepared=[]
   for i,f in enumerate(frames):
    f=f.resize((max(1,round(f.width*scale)),max(1,round(f.height*scale))),Image.Resampling.LANCZOS)
    out=Image.new('RGBA',(512,512));out.alpha_composite(f,((512-f.width)//2,492-f.height));buffer=BytesIO();out.save(buffer,format="PNG",optimize=True);destination=assets/f"pack_{key}_{i}.png";destination.write_bytes(buffer.getvalue());prepared.append(out)
    if key in ('walk','run','bored_shuffle'):
     buffer=BytesIO();ImageOps.mirror(out).save(buffer,format='PNG',optimize=True);(assets/f'pack_{key}_left_{i}.png').write_bytes(buffer.getvalue())
   duration=1.0 if key in SLOW else .11 if key in ('walk','run') else .28 if key=='water_offer' else .3
   manifest[key]={'sheet':f'sprites/{sheet}.png','frames':count,'seconds_per_frame':duration,'mode':'loop' if key in LOOPS else 'once_hold','label':key.replace('_',' ').title(),'edge_only':key=='bamboo_hang','crop_rectangles':crop_records,'shared_scale':scale,'mirrored_frame_indices':[2] if key in ('wave','greeting') else []}
   gif=[]
   for frame in prepared:
    frame=frame.copy();frame.thumbnail((180,180));background=Image.new('RGB',(220,220),'#eee8ff');background.paste(frame,(20,20),frame);gif.append(background)
   gif[0].save(previews/f'{key}.gif',save_all=True,append_images=gif[1:]+([gif[-1]]*3 if key not in LOOPS else []),duration=int(duration*1000),loop=0)
 manifest['happy_idle']['frame_seconds']=[3.0,1.0,.12,.12,3.0,.12]
 (assets/'sprite_collection_manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
 assert len(manifest)==47 and sum(m['frames'] for m in manifest.values())==240
 print('Prepared 17 sheets, 47 sequences, 240 poses; 16 mirrored walking/running frames.')
if __name__=='__main__':prepare(Path(sys.argv[1]),Path(sys.argv[2]),Path(sys.argv[3]))
