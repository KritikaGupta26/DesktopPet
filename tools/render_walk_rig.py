"""Render a textured puppet walk with deterministic limb coordination and foot contact."""
from pathlib import Path
from io import BytesIO
import math,json
import numpy as np
from scipy.ndimage import label,find_objects
from PIL import Image,ImageOps
ROOT=Path(__file__).resolve().parents[1]
COUNT=32

def foot(phase):
    phase%=1
    if phase<.6:return (40-80*phase/.6,0,True)
    u=(phase-.6)/.4
    return (-40+80*(u*u*(3-2*u)),-28*math.sin(math.pi*u),False)

def render():
    atlas=Image.open(ROOT/'artwork/panda_walk_rig_atlas.png').convert('RGBA')
    a=np.array(atlas);labs,_=label(a[:,:,3]>64);counts=np.bincount(labs.ravel());pieces={}
    for i,b in enumerate(find_objects(labs),1):
        if counts[i]<2000:continue
        x=(b[1].start+b[1].stop)/2;y=(b[0].start+b[0].stop)/2
        col=min(2,int(x/atlas.width*3));row=0 if y<570 else 1 if y<885 else 2
        mask=(labs==i);arr=a.copy();arr[:,:,3]=np.where(mask,arr[:,:,3],0)
        piece=Image.fromarray(arr);piece=piece.crop(piece.getchannel('A').getbbox())
        if (row,col) not in pieces or counts[i]>pieces[(row,col)][0]:pieces[(row,col)]=(counts[i],piece)
    assert len(pieces)==9,pieces.keys()
    pieces={key:value[1] for key,value in pieces.items()}
    body=pieces[0,0];body=body.resize((round(body.width*360/body.height),360),Image.Resampling.LANCZOS)
    frames=[];records=[]
    def center(out,img,x,y):out.alpha_composite(img,(round(x-img.width/2),round(y-img.height/2)))
    def segment(out,img,start,end,width):
        dx=end[0]-start[0];dy=end[1]-start[1];length=math.hypot(dx,dy)
        tex=img.resize((width,round(length+28)),Image.Resampling.LANCZOS)
        tex=tex.rotate(math.degrees(math.atan2(dx,dy)),Image.Resampling.BICUBIC,expand=True)
        center(out,tex,(start[0]+end[0])/2,(start[1]+end[1])/2)
    for i in range(COUNT):
        phase=i/COUNT;out=Image.new('RGBA',(512,512));bob=3*math.cos(4*math.pi*phase)
        metrics={}
        def leg(near):
            shift=0 if near else .5;dx,dy,stance=foot(phase+shift)
            hip=(250 if near else 283,356+bob);ankle=(hip[0]+dx,465+dy)
            vx=ankle[0]-hip[0];vy=ankle[1]-hip[1];d=math.hypot(vx,vy);l1=72;l2=70
            along=(l1*l1-l2*l2+d*d)/(2*d);height=math.sqrt(max(0,l1*l1-along*along))
            knee=(hip[0]+vx*along/d+vy*height/d,hip[1]+vy*along/d-vx*height/d)
            row=1 if near else 2
            segment(out,pieces[row,0],hip,knee,66 if near else 59)
            segment(out,pieces[row,1],knee,ankle,59 if near else 53)
            shoe=pieces[row,2].resize((86 if near else 77,38 if near else 34),Image.Resampling.LANCZOS)
            center(out,shoe,ankle[0]+17,473+dy)
            metrics['near' if near else 'far']={'foot_dx':dx,'foot_lift':-dy,'stance':stance,'arm_dx':-dx*.85}
        def arm(near):
            dx,_,_=foot(phase+(0 if near else .5));start=(225 if near else 301,238+bob)
            end=(start[0]-dx*.85,start[1]+124)
            segment(out,pieces[0,1 if near else 2],start,end,70 if near else 61)
        arm(False);leg(False);leg(True)
        center(out,body,256,20+body.height/2+bob)
        arm(True)
        frames.append(out);records.append(metrics)
        for direction,image in [('right',out),('left',ImageOps.mirror(out))]:
            buffer=BytesIO();image.save(buffer,format='PNG',optimize=True)
            (ROOT/'assets'/f'rig_walk_{direction}_{i}.png').write_bytes(buffer.getvalue())
    (ROOT/'assets/walk_rig_motion.json').write_text(json.dumps({'frames':COUNT,'motion':records},indent=2))
    preview=[]
    for image in frames:
        image=image.resize((180,180),Image.Resampling.LANCZOS)
        bg=Image.new('RGB',(220,200),'#eee8ff');bg.paste(image,(20,8),image);preview.append(bg)
    buf=BytesIO();preview[0].save(buf,format='GIF',save_all=True,append_images=preview[1:],duration=45,loop=0)
    (ROOT/'artwork/walk_rig_preview.gif').write_bytes(buf.getvalue())
    contact=Image.new('RGB',(880,400),'#eee8ff')
    for j,i in enumerate(range(0,32,4)):contact.paste(preview[i],((j%4)*220,(j//4)*200))
    contact.save(ROOT/'artwork/walk_rig_contact.png')
if __name__=='__main__':render()
