"""Drape one continuous generated ghost cloak over each existing panda pose."""
import math
from PIL import Image, ImageChops, ImageDraw, ImageOps


def dress_ghost(image, cloth, geometry, key):
    head, torso, profile, left = geometry
    hl, ht, hr, hb = head
    tl, tt, tr, tb = torso
    hx, hy = (hl+hr)/2, (ht+hb)/2
    tx, ty = (tl+tr)/2, (tt+tb)/2
    dx, dy = tx-hx, ty-hy
    angle = 0
    if dy < -15 and abs(dy) >= abs(dx)*.7:
        angle = 180
    elif key.startswith(("pack_sleep_", "pack_snore_sleep_", "pack_side_roll_", "pack_sploot_", "pack_forward_roll_", "pack_wake_", "pack_carry_bamboo_0", "pack_kung_fu_4")) and abs(dx) > abs(dy)*1.2 and abs(dx)>20:
        angle = 90 if dx>0 else -90
    head_width, head_height = hr-hl, hb-ht
    if angle in (90,-90):
        head_width, head_height = head_height, head_width
    canvas_size = (image.width*3, image.height*3)
    cx, cy = canvas_size[0]/2, canvas_size[1]/2
    distance = math.hypot(dx,dy)
    body_x = cx+(dx if angle==0 else 0)
    body_y = cy+(dy if angle==0 else distance)
    body_extent = (tb-tt if angle in (0,180) else tr-tl)/2
    neck_y = cy+head_height/2+5
    bottom_y = max(neck_y+12, body_y+body_extent+5)
    mid_y = max(neck_y+4, min(bottom_y-4,body_y+3))
    if left:
        cloth = ImageOps.mirror(cloth)
    face_anchor = (.28 if left else .72) if profile else .5
    upper_width = min(168,head_width*(1.75 if profile else 1.85))
    hem_width = min(150,max(head_width*1.25,(tr-tl)*1.45))
    # Continuous horizontal bands share boundaries. There is no detached
    # hood/bib seam; long folds survive the pose-dependent drape.
    rows = [(0,cy-head_height/2-14,cx,face_anchor,upper_width),
            (.22,cy,cx,face_anchor,upper_width),
            (.40,neck_y,body_x,.5,upper_width*.90),
            (.68,mid_y,body_x,.5,hem_width),
            (1,bottom_y,body_x,.5,hem_width)]
    mesh=[]
    for a,b in zip(rows,rows[1:]):
        sy0,y0,x0,anchor0,w0=a;sy1,y1,x1,anchor1,w1=b
        y0,y1=round(y0),round(y1)
        if y1<=y0:continue
        left0=x0-anchor0*w0;left1=x1-anchor1*w1
        sx00=-left0/w0*cloth.width;sx01=(canvas_size[0]-left0)/w0*cloth.width
        sx10=-left1/w1*cloth.width;sx11=(canvas_size[0]-left1)/w1*cloth.width
        mesh.append(((0,y0,canvas_size[0],y1),(sx00,sy0*cloth.height,sx10,sy1*cloth.height,
                     sx11,sy1*cloth.height,sx01,sy0*cloth.height)))
    layer=cloth.transform(canvas_size,Image.Transform.MESH,mesh,Image.Resampling.BICUBIC)
    if angle:
        layer=layer.rotate(angle,Image.Resampling.BICUBIC,center=(cx,cy))
    x0,y0=round(cx-hx),round(cy-hy)
    layer=layer.crop((x0,y0,x0+image.width,y0+image.height))
    preserve=Image.new('L',image.size)
    values=[]
    for y in range(image.height):
        for x in range(image.width):
            r,g,b,a=image.getpixel((x,y))
            prop=(b>r*1.10 and b>g*.95 or g>r*1.10 and g>b*1.10
                  or max(r,g,b)>=160 and max(r,g,b)-min(r,g,b)>90 and min(r,g,b)<130
                  or key.startswith(('scene_log_','scene_peekaboo_','pack_sit_on_log_','pack_balance_on_log_')) and r>90 and r>g*1.15 and g>b*1.3)
            dark=max(r,g,b)<125
            limb=dark and (y< hb-4 or y>=tb-1 or x<tl+8 or x>tr-8)
            values.append(255 if a>=128 and (prop or limb) else 0)
    preserve.putdata(values)
    # Open the face in the correct travel direction. The generated opening
    # remains the rim; this protects the original eyes, nose and expression.
    draw=ImageDraw.Draw(preserve)
    if profile:
        draw.ellipse((hl-8 if left else hl+(hr-hl)*.20,ht+(hb-ht)*.14,
                      hr-(hr-hl)*.20 if left else hr+8,hb+2),fill=255)
    else:
        draw.ellipse((hl+(hr-hl)*.08,ht+(hb-ht)*.14,hr-(hr-hl)*.08,hb-3),fill=255)
    layer.putalpha(ImageChops.subtract(layer.getchannel('A'),preserve))
    out=Image.alpha_composite(image,layer)
    out.putalpha(out.getchannel('A').point(lambda a:255 if a>=128 else 0))
    return out
