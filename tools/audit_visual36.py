"""Render all installed pose families and retain review evidence for v36."""
from pathlib import Path
import json, runpy, sys
from PIL import Image, ImageChops, ImageDraw
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from wardrobe import Wardrobe
from playful_activities import compose_mirror

OUT=Path(sys.argv[1]) if len(sys.argv)>1 else ROOT.parent/'review_v36'
OUT.mkdir(parents=True,exist_ok=True)
module=runpy.run_path(str(ROOT/'Start_Water_Puppy.pyw'))
manifest=json.loads((ROOT/'assets/sprite_collection_manifest.json').read_text())
sprites={}
for key,meta in manifest.items():
    scale=1
    if key in ('happy_idle','cursor_follow','petting','sad'):
        heights=[]
        for index in range(meta['frames']):
            image=Image.open(ROOT/'assets'/f'pack_{key}_{index}.png').convert('RGBA')
            box=image.getchannel('A').point(lambda a:255 if a>=128 else 0).getbbox()
            heights.append(box[3]-box[1])
        scale=450/max(heights)
    for index in range(meta['frames']):
        name=f'pack_{key}_{index}'
        image=Image.open(ROOT/'assets'/f'{name}.png').convert('RGBA')
        if scale!=1:image=module['normalize_pose_sprite'](image,scale)
        image=image.resize((180,180),Image.Resampling.LANCZOS)
        image.putalpha(image.getchannel('A').point(lambda a:255 if a>=128 else 0))
        sprites[name]=image
for kind in ('log','meditate','peekaboo'):
    for index in range(8):
        name=f'scene_{kind}_{index}'
        image=Image.open(ROOT/'assets'/f'{name}.png').convert('RGBA').resize((360 if kind=='peekaboo' else 180,180),Image.Resampling.LANCZOS)
        image.putalpha(image.getchannel('A').point(lambda a:255 if a>=128 else 0))
        sprites[name]=image
for index in range(8):sprites[f'pack_mirror_{index}']=Image.open(ROOT/'assets'/f'pack_mirror_{index}.png').convert('RGBA')
wardrobe=Wardrobe(ROOT/'assets')
records=[];ghost=[]
themes=list(json.loads((ROOT/'assets/wardrobe_manifest.json').read_text()))
for theme in themes:
    for name,image in sprites.items():
        result=wardrobe.dress(image,theme,name)
        present=ImageChops.difference(image.convert('RGB'),result.convert('RGB')).getbbox() is not None
        alpha=result.getchannel('A')
        corners=any(alpha.getpixel(p) for p in ((0,0),(image.width-1,0),(0,179),(image.width-1,179)))
        records.append({'theme':theme,'sprite':name,'costume_present':present,'opaque_corner':bool(corners)})
        if theme=='spooky':ghost.append((name,result))
    board=Image.new('RGB',(960,640),'#eee6dd');draw=ImageDraw.Draw(board)
    sample=['pack_happy_idle_0','pack_walk_0','pack_run_4','pack_water_offer_7','pack_bow_2','pack_sleep_0','pack_eat_bamboo_3','pack_hula_hoop_4','pack_mirror_3','pack_mirror_6','pack_sploot_2','pack_forward_roll_4']
    for index,name in enumerate(sample):
        result=wardrobe.dress(sprites[name],theme,name);x=index%4*240;y=index//4*210
        board.paste(result,(x+30,y+25),result);draw.text((x+4,y+4),name,fill='black')
    board.save(OUT/f'outfit_{theme}_audit.png')
    prop=Image.open(ROOT/'assets/mirror_prop.png').convert('RGBA')
    board=Image.new('RGB',(1440,400),'#eee6dd')
    for index in range(8):
        name=f'pack_mirror_{index}';result=compose_mirror(wardrobe.dress(sprites[name],theme,name),prop)
        board.paste(result,((index%4)*360,(index//4)*200),result)
    board.save(OUT/f'mirror_{theme}_review.png')
for index in range(8):
    name=f'scene_spooky_{index}'
    image=Image.open(ROOT/'assets'/f'{name}.png').convert('RGBA').resize((180,180),Image.Resampling.LANCZOS)
    image.putalpha(image.getchannel('A').point(lambda a:255 if a>=128 else 0))
    result=wardrobe.dress(image,'spooky',name);ghost.append((name,result))
    records.append({'theme':'spooky','sprite':name,'costume_present':True,'opaque_corner':any(result.getpixel(p)[3] for p in ((0,0),(179,0),(0,179),(179,179)))})
for page in range((len(ghost)+47)//48):
    board=Image.new('RGB',(1440,1260),'#eee6dd');draw=ImageDraw.Draw(board)
    for index,(name,image) in enumerate(ghost[page*48:(page+1)*48]):
        if image.width>180:image=image.resize((180,90),Image.Resampling.LANCZOS)
        x=index%8*180;y=index//8*210;board.paste(image,(x,y+25),image);draw.text((x+3,y+4),name,fill='black')
    board.save(OUT/f'ghost_all_{page+1}.png')
failures=[r for r in records if not r['costume_present'] or r['opaque_corner']]
report={'rendered_variants':len(records),'themes':len(themes),'ghost_poses_reviewed':len(ghost),'failures':failures,'records':records}
(OUT/'wardrobe_render_audit.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({k:v for k,v in report.items() if k!='records'}))
if failures:sys.exit(1)
