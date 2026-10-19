"""Shared, sequence-level sizing for the existing panda artwork."""
from statistics import median
from PIL import Image, ImageOps
from wardrobe import landmarks


def fit_sequence(sources, keys):
    """Keep head scale consistent without stretching bodies or cropping props.

    One scale applies to every frame, so breathing and bending cannot pump
    the character's size. A profile naturally projects narrower than a front
    face. Wide/raised props take precedence over enlargement.
    """
    if keys and all('_left_' in key for key in keys):
        fitted=fit_sequence([ImageOps.mirror(im) for im in sources],
                            [key.replace('_left_','_') for key in keys])
        def mirror_rect(rect):
            l,t,r,b=rect
            return (180-r,t,180-l,b)
        return [(ImageOps.mirror(im),(mirror_rect(g[0]),mirror_rect(g[1]),g[2],True) if g else None)
                for im,g in fitted]
    raw = [im.resize((180,180),Image.Resampling.LANCZOS) for im in sources]
    geometry = [landmarks(im,key) for im,key in zip(raw,keys)]
    widths = [g[0][2]-g[0][0] for g in geometry if g]
    profile = any(g and g[2] for g in geometry)
    scale = (92 if profile else 102)/median(widths) if widths else 1
    boxes = [im.getchannel('A').point(lambda a:255 if a>=128 else 0).getbbox() for im in raw]
    visible = [b for b in boxes if b]
    if visible:
        scale = min(scale,168/max(b[2]-b[0] for b in visible),164/max(b[3]-b[1] for b in visible))
    # Heuristic landmarks on acrobatic/occluded poses must never cause a
    # drastic resize. Their existing source proportions remain authoritative.
    scale = max(.90,min(1.20,scale))
    results=[]
    for source,box,g in zip(sources,boxes,geometry):
        if not box or not g:
            results.append((source.resize((180,180)),g));continue
        # Resample the original 512px texture, rather than enlarge a 180px copy.
        sw,sh=source.size
        resized=source.resize((round(sw*scale),round(sh*scale)),Image.Resampling.LANCZOS)
        bounds=resized.getchannel('A').point(lambda a:255 if a>=128 else 0).getbbox()
        dx=round((sw-resized.width)/2)
        margin=round(sw*6/180)
        dx=max(margin-bounds[0],min(dx,sw-margin-bounds[2]))
        dy=round(sh*172/180)-bounds[3]
        canvas=Image.new('RGBA',source.size)
        canvas.alpha_composite(resized,(dx,dy))
        out=canvas.resize((180,180),Image.Resampling.LANCZOS)
        out.putalpha(out.getchannel('A').point(lambda a:255 if a>=128 else 0))
        sx,sy=resized.width/sw,resized.height/sh
        def move(rect):
            l,t,r,b=rect
            return (round(l*sx+dx*180/sw),round(t*sy+dy*180/sh),
                    round(r*sx+dx*180/sw),round(b*sy+dy*180/sh))
        results.append((out,(move(g[0]),move(g[1]),g[2],g[3])))
    return results
