"""Package two generated four-pose half-cycles as one complete walk loop."""
from PIL import Image,ImageOps,ImageFilter
from pathlib import Path
import json,shutil
root=Path(__file__).resolve().parents[1]
archive=root/'artwork/v30_walk'
archive.mkdir(parents=True,exist_ok=True)
# The archive was populated before the first v31 candidate was exported.
for p in (root/'assets').glob('pack_walk*.png'):
    if not (archive/p.name).exists():
        shutil.copy2(p,archive/p.name)
frames=[];rects=[]
for source in ('walk_v31_first_half.png','walk_v31_opposite_half.png'):
    with Image.open(root/'artwork'/source) as opened:
        sheet=opened.convert('RGBA')
    row=[]
    for i in range(4):
        rect=(round(i*sheet.width/4),0,round((i+1)*sheet.width/4),sheet.height)
        frame=sheet.crop(rect)
        alpha=frame.getchannel('A')
        interior=alpha.point(lambda a:255 if a>=128 else 0).filter(ImageFilter.MinFilter(7))
        pixels=frame.load();safe=interior.load()
        for y in range(frame.height):
            for x in range(frame.width):
                r,g,b,a=pixels[x,y]
                if safe[x,y]==0 and max(r,g,b)-min(r,g,b)>170 and a>0:
                    pixels[x,y]=(r,g,b,0)
        box=frame.getchannel('A').point(lambda a:255 if a>=128 else 0).getbbox()
        if not box:raise ValueError(f'Empty walk pose {source}:{i}')
        # Preserve a common head anchor rather than centering variable stride
        # widths, which otherwise makes the torso rock sideways every frame.
        upper=frame.getchannel('A').point(lambda a:255 if a>=128 else 0).crop((0,box[1],frame.width,box[1]+round((box[3]-box[1])*.40)))
        head=upper.getbbox();head_x=(head[0]+head[2])/2-box[0]
        row.append((frame.crop(box),head_x))
        rects.append({'source':source,'rect':list(rect)})
    scale=min(450/max(im.height for im,hx in row),460/max(im.width for im,hx in row))
    for im,hx in row:
        scaled=im.resize((round(im.width*scale),round(im.height*scale)),Image.Resampling.LANCZOS)
        x=round(286-hx*scale)
        x=max(12,min(x,500-scaled.width))
        out=Image.new('RGBA',(512,512))
        out.alpha_composite(scaled,(x,489-scaled.height))
        frames.append(out)
# The generated fourth cells do not yet have trustworthy leg occlusion.
# Keep packaging slots valid with held contact poses; playback selects only
# six approved contact/down/passing poses from the two opposite half-cycles.
frames[3] = frames[4].copy()
frames[7] = frames[0].copy()
for i,out in enumerate(frames):
    out.save(root/f'assets/pack_walk_{i}.png')
    ImageOps.mirror(out).save(root/f'assets/pack_walk_left_{i}.png')
manifest_path=root/'assets/sprite_collection_manifest.json'
manifest=json.loads(manifest_path.read_text())
manifest['walk'].update(generated_source='artwork/walk_v31_first_half.png',
    generated_sources=['artwork/walk_v31_first_half.png','artwork/walk_v31_opposite_half.png'],
    previous_frames='artwork/v30_walk',crop_rectangles=rects,selected_playback_frames=[0,1,2,4,5,6],
    head_anchor_x=286,ground_anchor_y=489)
manifest_path.write_text(json.dumps(manifest,indent=2))
for direction in ('right','left'):
    sequence=[]
    for i in [0,1,2,4,5,6]:
        im=Image.open(root/f'assets/pack_walk{"_left" if direction=="left" else ""}_{i}.png').convert('RGBA')
        im.thumbnail((180,180),Image.Resampling.LANCZOS)
        bg=Image.new('RGB',(220,220),'#f4eadd');bg.paste(im,(20,20),im);sequence.append(bg)
    sequence[0].save(root/f'artwork/walk_v31_{direction}.gif',save_all=True,append_images=sequence[1:],duration=240,loop=0)
print('Prepared 8 half-cycle poses with opposite limb swing and shared head/ground anchors.')
