"""Render the actual runtime sprites, with no separate preview fitting path."""
from pathlib import Path
from unittest.mock import patch
import json, runpy, sys
from PIL import Image, ImageDraw, ImageFont

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
OUT=Path(sys.argv[1]).resolve() if len(sys.argv)>1 else ROOT.parent/'appearance_preview'
OUT.mkdir(parents=True,exist_ok=True)
M=runpy.run_path(str(ROOT/'Start_Water_Puppy.pyw'))
pet=M['WaterPet'].__new__(M['WaterPet']);pet.app_dir=ROOT
with patch('PIL.ImageTk.PhotoImage',side_effect=lambda image:image):
    pet._load_images()

FONT=Path('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf')
def font(size):
    return ImageFont.truetype(str(FONT),size) if FONT.exists() else ImageFont.load_default()

def board(themes,title):
    canvas=Image.new('RGB',(1020,145+205*len(themes)),'#f3f0ea')
    d=ImageDraw.Draw(canvas)
    d.text((28,22),title,font=font(27),fill='#253a38')
    d.text((28,62),'Same runtime artwork • consistent scale • costumes fitted to each pose',font=font(15),fill='#576b68')
    for col,label in enumerate(('Standing','Walking','Sitting','Sleeping')):
        d.text((164+col*210,108),label,font=font(18),fill='#253a38')
    keys=('pack_happy_idle_0','pack_walk_0','pack_sit_down_3','pack_sleep_0')
    for row,(theme,label) in enumerate(themes):
        y=145+row*205
        d.text((24,y+80),label,font=font(15),fill='#253a38')
        for col,key in enumerate(keys):
            x=145+col*210
            d.rounded_rectangle((x,y+3,x+194,y+193),radius=14,fill='#e7e5df')
            d.line((x+10,y+180,x+184,y+180),fill='#c5d0c7')
            im=pet.wardrobe.dress(pet.image_pil[key],theme,key)
            canvas.paste(im,(x+7,y+8),im)
    return canvas

themes=[('classic','Classic'),('diwali','Diwali'),('navratri','Navratri'),
        ('christmas','Christmas'),('spooky','Ghost')]
board(themes,'Water Panda | Appearance review').save(OUT/'Panda_Appearance_Preview.png')
all_themes=[('classic','Classic')]+[(t,t.replace('_',' ').title()) for t in json.loads((ROOT/'assets/wardrobe_manifest.json').read_text())]
board(all_themes,'Water Panda | All costume fits').save(OUT/'Panda_All_Themes.png')

# Four simultaneous pose loops make size changes and clothing jitter visible.
frames=[]
families=['happy_idle','walk','sit_down','sleep']
for tick in range(24):
    canvas=Image.new('RGB',(1020,405),'#f3f0ea');d=ImageDraw.Draw(canvas)
    d.text((28,20),'Water Panda | Pose and costume motion',font=font(25),fill='#253a38')
    for row,theme in enumerate(('classic','navratri')):
        for col,family in enumerate(families):
            count=pet.pack_manifest[family]['frames']
            index=([0,1,2,3,4,5][(tick//3)%6] if family=='happy_idle' else tick%count if family=='walk' else 3 if family=='sit_down' else (tick//4)%count)
            key=f'pack_{family}_{index}';im=pet.wardrobe.dress(pet.image_pil[key],theme,key)
            x=155+col*210;y=65+row*165
            # Smaller preview tiles use one uniform display scale only.
            im=im.resize((155,155),Image.Resampling.LANCZOS)
            canvas.paste(im,(x,y),im)
        d.text((25,120+row*165),theme.title(),font=font(16),fill='#253a38')
    frames.append(canvas)
frames[0].save(OUT/'Panda_Pose_Motion.gif',save_all=True,append_images=frames[1:],duration=150,loop=0,disposal=2)

records=[]
themes=list(json.loads((ROOT/'assets/wardrobe_manifest.json').read_text()))
if '--preview-only' in sys.argv:
    print('Previews rendered from runtime loader.')
    raise SystemExit(0)
if '--ghost-only' in sys.argv:
    themes=['spooky']
for name,im in pet.image_pil.items():
    if not name.startswith(('pack_','scene_')):continue
    for theme in themes:
        out=pet.wardrobe.dress(im,theme,name)
        box=out.getchannel('A').getbbox()
        records.append({'pose':name,'theme':theme,'bounds':box,
                        'edge_clipped':bool(box and (box[0]<=0 or box[1]<=0 or box[2]>=out.width or box[3]>=out.height))})
failures=[r for r in records if r['edge_clipped']]
report={'rendered_variants':len(records),'edge_failures':failures,
        'source_commit':'a5acb6424dd8d79796a1563e948fb96485a281c1',
        'limitations':['Offline renders; Windows app/installer has not been rebuilt or launched for this change.',
                       'Size checks cannot certify every artistic detail.'], 'records':records}
(OUT/'appearance_validation.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({k:v for k,v in report.items() if k not in ('records','edge_failures')},ensure_ascii=True))
print('Edge failures:',len(failures))
if failures:raise SystemExit(1)
