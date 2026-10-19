"""Render a closed bedsheet ghost; expose only its face and activity props."""
import math
from PIL import Image, ImageChops, ImageDraw, ImageOps, ImageFilter


def resting_sheet(image, cloth, head, torso):
    """Drape a continuous hood/blanket over a horizontal resting body.

    Rotating the standing five-band mesh made its hem become a vertical,
    accordion-like edge. Keep gravity vertical and broaden the lower folds
    instead, using the same shaded cloth texture as the standing costume.
    """
    hl, ht, hr, hb = head
    tl, tt, tr, tb = torso
    bounds = image.getchannel('A').getbbox()
    hx = (hl+hr)/2
    ground = min(image.height-3, bounds[3]+2)
    top = max(3, min(ht-15, bounds[1]-3))
    left = max(3, min(bounds[0]-4, hl-12))
    right = min(image.width-3, max(bounds[2]+4, tr+5))
    # The standing face opening cannot become an extra hole in a blanket.
    # Close internal transparent regions with a shaded fabric strip; the
    # actual resting face is restored once, after the drape is fitted.
    cloth=cloth.copy()
    alpha=cloth.getchannel('A')
    outside=alpha.point(lambda a:255 if a<128 else 0)
    border=[(x,0) for x in range(cloth.width)]+[(x,cloth.height-1) for x in range(cloth.width)]
    border += [(0,y) for y in range(cloth.height)]+[(cloth.width-1,y) for y in range(cloth.height)]
    for point in border:
        if outside.getpixel(point)==255:
            ImageDraw.floodfill(outside,point,128)
    holes=outside.point(lambda a:255 if a==255 else 0)
    fabric=cloth.crop((round(cloth.width*.25),0,round(cloth.width*.35),cloth.height)).resize(cloth.size,Image.Resampling.BICUBIC)
    cloth.paste(fabric,(0,0),holes)
    rows = [(0, top, hx-65, hx+65),
            (.20, top+(ground-top)*.25, hx-65, min(right,hx+65)),
            (.45, top+(ground-top)*.55, left, right),
            (.72, top+(ground-top)*.80, left, right),
            (1, ground, left+2, right-2)]
    mesh=[]
    for (sy0,y0,l0,r0),(sy1,y1,l1,r1) in zip(rows,rows[1:]):
        y0,y1=round(y0),round(y1)
        if y1<=y0:continue
        w0,w1=r0-l0,r1-l1
        mesh.append(((0,y0,image.width,y1),
                     (-l0/w0*cloth.width,sy0*cloth.height,
                      -l1/w1*cloth.width,sy1*cloth.height,
                      (image.width-l1)/w1*cloth.width,sy1*cloth.height,
                      (image.width-l0)/w0*cloth.width,sy0*cloth.height)))
    return cloth.transform(image.size,Image.Transform.MESH,mesh,Image.Resampling.BICUBIC)


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
    bounds=image.getchannel('A').point(lambda a:255 if a>=128 else 0).getbbox()
    if angle == 0:
        # Floor-length sheet follows the actual pose baseline, including feet.
        # Props (log/pillar/bamboo) must not determine costume length.
        foot_bottom = min(image.height-4, max(tb+12, bounds[3] if bounds else tb+12))
        if key.startswith(('scene_log_', 'scene_peekaboo_', 'pack_sit_on_log_', 'pack_balance_on_log_', 'pack_bamboo_hang_')):
            foot_bottom = min(image.height-4, tb+16)
        bottom_y = max(neck_y+12, cy+foot_bottom-hy)
    else:
        bottom_y = max(neck_y+12, body_y+body_extent+9)
    mid_y = max(neck_y+4, min(bottom_y-4,body_y+3))
    if left:
        cloth = ImageOps.mirror(cloth)
    face_anchor = (.28 if left else .72) if profile else .5
    upper_width = min(260,head_width*(2.10 if profile else 2.40))
    hem_width = min(158,max(head_width*1.55,(tr-tl)*1.60))
    # Continuous horizontal bands share boundaries. There is no detached
    # hood/bib seam; long folds survive the pose-dependent drape.
    rows = [(0,cy-head_height/2-9,cx,face_anchor,upper_width),
            (.22,cy,cx,face_anchor,upper_width),
            (.40,neck_y,body_x,.5,upper_width*.90),
            (.68,mid_y,body_x,.5,max(hem_width,upper_width*.85)),
            (1,bottom_y,body_x,.5,hem_width)]
    if profile:
        # The cutout already contains the profile silhouette. Changing the
        # horizontal source anchor at the neck introduced a visible zigzag.
        rows=[(sy,y,x,face_anchor,width) for sy,y,x,anchor,width in rows]
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
    # Fit the complete garment while it is still on the oversized canvas.
    # Moving pixels after cropping cannot recover a severed hem or hood.
    full_bounds=layer.getchannel('A').point(lambda a:255 if a>=128 else 0).getbbox()
    if full_bounds:
        bl,bt,br,bb=full_bounds
        scale=min(1,(image.width-6)/(br-bl),(image.height-6)/(bb-bt))
        nl,nr=cx+(bl-cx)*scale,cx+(br-cx)*scale
        nt,nb=cy+(bt-cy)*scale,cy+(bb-cy)*scale
        shift_x=max(x0+3-nl,min(0,x0+image.width-3-nr))
        shift_y=max(y0+3-nt,min(0,y0+image.height-3-nb))
        if scale<1 or shift_x or shift_y:
            layer=layer.transform(canvas_size,Image.Transform.AFFINE,
                                  (1/scale,0,cx-(cx+shift_x)/scale,
                                   0,1/scale,cy-(cy+shift_y)/scale),
                                  Image.Resampling.BICUBIC)
    layer=layer.crop((x0,y0,x0+image.width,y0+image.height))
    if key.startswith(('pack_sleep_', 'pack_snore_sleep_')):
        layer=resting_sheet(image,cloth,head,torso)
    # The full original body must never be composited underneath the sheet:
    # that is what exposed the black arms, feet, and straight neck band in v35.
    # Retain just the original face and the meaningful foreground prop.
    preserve=Image.new('L',image.size)
    values=[]
    glass = key.startswith(('pack_water_offer_', 'pack_alternate_offer_', 'pack_drink_water_'))
    bamboo = key.startswith(('pack_eat_bamboo_', 'pack_carry_bamboo_', 'pack_bamboo_hang_'))
    hoop = key.startswith(('pack_hula_hoop_', 'pack_alternate_hoop_'))
    wood = key.startswith(('scene_log_', 'scene_peekaboo_', 'pack_sit_on_log_', 'pack_balance_on_log_'))
    watch = key.startswith('pack_watch_')
    pumpkin = key.startswith('scene_spooky_')
    glass_pixels=[]
    wood_pixels=[]
    for y in range(image.height):
        for x in range(image.width):
            r,g,b,a=image.getpixel((x,y))
            blue=b>105 and g>50 and b>r*1.10 and b>g*.95
            green=g>r*1.10 and g>b*1.10
            colour=max(r,g,b)>=160 and max(r,g,b)-min(r,g,b)>90 and min(r,g,b)<130
            brown=r>90 and r>g*1.15 and g>b*1.3
            prop=((glass and blue) or (bamboo and green)
                  or (hoop and tt-15<=y<=tb and (blue or green or (r>135 and r>g*1.8 and r>b*1.8)))
                  or ((wood and y>=tb+1 or watch) and brown)
                  or (pumpkin and y>110 and r>150 and r>g*1.25 and g>b*1.5)
                  or (pumpkin and 70<x<112 and 115<y<145 and max(r,g,b)>130 and max(r,g,b)-min(r,g,b)<22))
            values.append(255 if a>=128 and prop else 0)
            if glass and a>=128 and blue:
                glass_pixels.append((x,y))
            if wood and a>=128 and brown and y>=tb+1:
                wood_pixels.append((x,y))
    preserve.putdata(values)
    if glass_pixels:
        draw=ImageDraw.Draw(preserve)
        # Preserve clear glass rim and water, not only saturated blue marks.
        xs,ys=zip(*glass_pixels)
        draw.rectangle((min(xs)-1,min(ys)-1,max(xs)+1,max(ys)+1),fill=255)
    if wood_pixels:
        xs,ys=zip(*wood_pixels)
        for y in range(min(ys),max(ys)+1):
            for x in range(min(xs),max(xs)+1):
                r,g,b,a=image.getpixel((x,y))
                if a>=128 and (max(r,g,b)>110 or r>50 and r>g*1.15 and g>b*1.15):
                    preserve.putpixel((x,y),255)
    # Dark neutral fur belongs to the concealed panda, even when it overlaps
    # a prop's rectangle. Close small gaps and fill paw-pad/belly holes so those
    # are not accidentally restored along with glass or wood grain.
    concealed=Image.new('L',image.size)
    concealed.putdata([255 if a>=128 and max(r,g,b)<125 and max(r,g,b)-min(r,g,b)<35 and y>hb-2 else 0
                      for y in range(image.height) for x in range(image.width)
                      for r,g,b,a in [image.getpixel((x,y))]])
    concealed=concealed.filter(ImageFilter.MaxFilter(3))
    outside=ImageChops.invert(concealed)
    ImageDraw.floodfill(outside,(0,0),128)
    holes=outside.point(lambda value:255 if value==255 else 0)
    concealed=ImageChops.lighter(concealed,holes)
    preserve=ImageChops.subtract(preserve,concealed)
    draw=ImageDraw.Draw(preserve)
    if profile:
        draw.ellipse((hl-8 if left else hl+(hr-hl)*.20,ht+(hb-ht)*.14,
                      hr-(hr-hl)*.20 if left else hr+8,hb+2),fill=255)
    else:
        draw.ellipse((hl+(hr-hl)*.08,ht+(hb-ht)*.14,hr-(hr-hl)*.08,hb-3),fill=255)
    foreground=image.copy()
    foreground.putalpha(ImageChops.multiply(image.getchannel('A'),preserve))
    out=Image.alpha_composite(layer,foreground)
    out.putalpha(out.getchannel('A').point(lambda a:255 if a>=128 else 0))
    return out
