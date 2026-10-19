"""Review the bundled cute character through the actual runtime loader."""
from pathlib import Path
from unittest.mock import patch
import json
import runpy
import sys
from PIL import Image, ImageDraw, ImageFont

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from character_routines import STORIES, story_duration, story_pose

OUT=Path(sys.argv[1]).resolve() if len(sys.argv)>1 else ROOT/'artwork/v38/review'
OUT.mkdir(parents=True,exist_ok=True)
M=runpy.run_path(str(ROOT/'Start_Water_Puppy.pyw'))
pet=M['WaterPet'].__new__(M['WaterPet']);pet.app_dir=ROOT
with patch('PIL.ImageTk.PhotoImage',side_effect=lambda im:im):pet._load_images()
fontpath='/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
def font(size):return ImageFont.truetype(fontpath,size)
names=['happy_idle','walk','sit_down','sleep','noodles','dumpling_balance',
       'staff_ready','staff_turn','butterfly','doodle','hero_landing','bashful']
def board(theme):
    out=Image.new('RGB',(920,820),'#f5f1eb');draw=ImageDraw.Draw(out)
    draw.text((25,18),'Water Panda | Existing character, new performances',font=font(23),fill='#303848')
    draw.text((25,52),theme.title()+' · rendered with the application loader and costume fitter',font=font(15),fill='#67686b')
    for i,name in enumerate(names):
        x=25+(i%4)*225;y=90+(i//4)*235
        draw.rounded_rectangle((x,y,x+207,y+205),14,fill='#e6e4e1')
        key=f'pack_{name}_0';im=pet.wardrobe.dress(pet.image_pil[key],theme,key)
        out.paste(im,(x+14,y+15),im)
        draw.text((x+5,y+210),name.replace('_',' ').title(),font=font(14),fill='#303848')
    return out
for theme in ('classic','navratri','spooky'):
    board(theme).save(OUT/f'Panda_v38_{theme}.png')

records=[]
extension_keys=[name for name in pet.image_pil
                if name.startswith('pack_') and name.split('_',1)[1].rsplit('_',1)[0]
                in {pose for _,timeline in STORIES.values() for pose,_ in timeline}]
themes=['classic']+list(json.loads((ROOT/'assets/wardrobe_manifest.json').read_text()))
if '--preview-only' not in sys.argv:
    for theme in themes:
        for key in extension_keys:
            im=pet.wardrobe.dress(pet.image_pil[key],theme,key)
            box=im.getchannel('A').getbbox()
            if not box or box[0]<=0 or box[1]<=0 or box[2]>=im.width or box[3]>=im.height:
                records.append({'theme':theme,'pose':key,'bounds':box})
report={'variants_checked':len(themes)*len(extension_keys),'clipping_failures':records,
        'windows_launch_verified':False,'new_core_character':False,
        'new_extension_poses':16,'new_performance_timelines':len(STORIES)}
if '--preview-only' not in sys.argv:
    (OUT/'render_report.json').write_text(json.dumps(report,indent=2)+'\n')

# Actual keyframe playback, not a claim of new motion-capture/inbetween frames.
frames=[]
keys=['kungfu_story','noodles','staff_practice','doodle']
for tick in range(100):
    out=Image.new('RGB',(840,260),'#f5f1eb');d=ImageDraw.Draw(out)
    for col,key in enumerate(keys):
        elapsed=(tick*.12)%story_duration(key)
        family,local=story_pose(key,elapsed);meta=pet.pack_manifest[family]
        index=min(meta['frames']-1,int(local/meta['seconds_per_frame']))
        if meta['mode']=='loop':index=int(local/meta['seconds_per_frame'])%meta['frames']
        name=f'pack_{family}_{index}';im=pet.image_pil[name]
        out.paste(im,(col*210+15,25),im)
        d.text((col*210+12,218),STORIES[key][0],font=font(13),fill='#303848')
    frames.append(out)
frames[0].save(OUT/'Panda_v38_performances.gif',save_all=True,append_images=frames[1:],duration=120,loop=0,disposal=2)
print(json.dumps(report))
if records:raise SystemExit(1)
