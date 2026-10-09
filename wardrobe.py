"""Fit shaded costume components to each animated body, preserving foreground paws."""
from collections import OrderedDict
from ghost_cloak import dress_ghost
from PIL import Image, ImageChops, ImageDraw, ImageOps


def fur_components(image):
    pixels = list(image.getdata())
    width, height = image.size
    remaining = {i for i,(r,g,b,a) in enumerate(pixels)
                 if a >= 128 and r > 150 and g > 130 and b > 110 and r-b < 75}
    groups = []
    while remaining:
        first = remaining.pop()
        stack, points = [first], []
        while stack:
            point = stack.pop()
            x, y = point % width, point // width
            points.append((x,y))
            for other in (point-1 if x else -1, point+1 if x+1<width else -1,
                          point-width if y else -1, point+width if y+1<height else -1):
                if other in remaining:
                    remaining.remove(other)
                    stack.append(other)
        if len(points) > 20:
            xs,ys = zip(*points)
            groups.append((len(points), (min(xs),min(ys),max(xs)+1,max(ys)+1)))
    return sorted(groups, reverse=True)


def landmarks(image, key):
    groups = fur_components(image)
    opaque = image.getchannel("A").getbbox()
    if not opaque:
        return None
    large = groups[:5]
    if large:
        candidates=[g for g in large if g[0]>=max(150,large[0][0]*.25)]
        head = min(candidates or large,key=lambda g:g[1][1])[1]
    else:
        head=(opaque[0],opaque[1],opaque[2],opaque[1]+int((opaque[3]-opaque[1])*.5))
    bodies=[g for g in groups if g[1]!=head and g[0]>35]
    if bodies:
        torso=max(bodies,key=lambda g:g[0])[1]
    else:
        l,t,r,b=head
        torso=(int(l+(r-l)*.25),b-1,int(r-(r-l)*.20),opaque[3]-5)
    if torso[3]<=torso[1]+3:
        torso=(opaque[0]+10,opaque[1]+int((opaque[3]-opaque[1])*.55),opaque[2]-10,opaque[3]-6)
    profile=key.startswith(("pack_walk", "pack_run", "pack_bored_shuffle"))
    # Review overrides for poses where fur regions join or the body is occluded.
    overrides={
        "pack_water_offer_6":((43,24,135,95),(64,103,122,150)),
        "pack_water_offer_7":((43,24,135,94),(65,107,127,153)),
        "pack_alternate_offer_3":((44,32,134,100),(63,105,126,154)),
        "pack_alternate_offer_4":((43,34,130,103),(60,111,120,156)),
        "pack_drink_water_4":((44,31,134,103),(65,113,129,158)),
        "pack_sploot_0":((43,110,131,169),(80,64,130,115)),
        "pack_sploot_1":((45,129,135,174),(75,91,135,135)),
        "pack_sploot_2":((45,133,125,177),(114,144,162,172)),
        "pack_sploot_3":((48,137,123,178),(122,146,162,172)),
        "pack_wake_up_0":((43,114,109,166),(103,123,139,164)),
        "pack_fetch_1":((37,57,136,122),(76,121,127,151)),
        "pack_fetch_2":((45,49,140,122),(68,123,126,157)),
        "scene_log_3":((50,64,135,132),(66,124,125,137)),
        "pack_forward_roll_1":((46,48,128,115),(62,116,111,146)),
        "pack_forward_roll_2":((44,83,138,156),(61,58,120,87)),
        "pack_forward_roll_3":((102,68,164,160),(59,60,115,109)),
        "pack_forward_roll_4":((47,93,137,165),(60,47,127,99)),
        "pack_forward_roll_6":((45,66,138,140),(61,48,120,78)),
        "scene_peekaboo_2":((116,60,210,114),(123,114,209,151)),
        "scene_peekaboo_3":((97,36,154,115),(135,113,203,151)),
        "scene_peekaboo_4":((116,60,210,113),(117,114,210,152)),
        "scene_peekaboo_5":((174,34,242,112),(132,111,221,147)),
    }
    spooky_heads=[(56,42,124,94),(56,41,124,94),(49,73,126,122),(54,58,126,116),(48,42,136,119),(48,42,136,120),(48,42,136,120),(48,42,136,120)]
    if key.startswith("scene_spooky_"):
        index=int(key.rsplit("_",1)[1])
        overrides[key]=(spooky_heads[index],(55,115,130,155))
    if key in overrides:
        head,torso=overrides[key]
    if key.startswith("pack_sleep_"):
        head=(44,107,135,162)
        torso=(121,120,158,153)
    return head,torso,profile,key.startswith(("pack_walk_left", "pack_run_left", "pack_bored_shuffle_left"))


class Wardrobe:
    def __init__(self, assets):
        self.assets=assets
        self.parts={}
        self.geometry={}
        self.cache=OrderedDict()

    def part(self, theme, name):
        cache_key=(theme,name)
        if cache_key not in self.parts:
            path=self.assets/f"wardrobe_{theme}_{name}.png"
            self.parts[cache_key]=Image.open(path).convert("RGBA") if path.exists() else None
        return self.parts[cache_key]

    def dress(self, image, theme, key):
        if theme == "classic":
            return image
        if key not in self.geometry:
            self.geometry[key]=landmarks(image,key)
        geometry=self.geometry[key]
        if geometry is None:
            return image
        head,torso,profile,left=geometry
        if theme == "spooky":
            return dress_ghost(image, self.part(theme, "full_profile" if profile else "full_front"), geometry, key)
        out=image.copy()
        l,t,r,b=torso
        hl,ht,hr,hb=head
        name="profile" if profile else "front"
        cloth=self.part(theme,name)
        if cloth is None:
            raise ValueError(f"Missing persistent outfit: {theme}/{name}")
        scarf=theme in ("autumn","thanksgiving","christmas","valentine","birthday","shiva","spring","summer","winter")
        lying=key.startswith(("pack_sleep_","pack_snore_sleep_")) or key in ("pack_sploot_2","pack_sploot_3","pack_wake_up_0","pack_wake_up_1")
        inverted=key in ("pack_forward_roll_2","pack_forward_roll_3","pack_forward_roll_4","pack_forward_roll_6","pack_sploot_0","pack_sploot_1")
        if lying or inverted:
            cloth=cloth.rotate(90 if lying else 180,expand=True)
            box=(l-3,t-3,r+4,b+4)
        elif scarf:
            width=max(15,int((hr-hl)*.75))
            height=max(12,int((hb-ht)*.34))
            box=(int((hl+hr-width)/2),hb-5,int((hl+hr+width)/2),hb-5+height)
        else:
            expand=max(3,int((r-l)*.14))
            box=(l-expand,max(ht+int((hb-ht)*.75),t-10),r+expand,b+4)
        garment=cloth.resize((max(1,box[2]-box[0]),max(1,box[3]-box[1])),Image.Resampling.LANCZOS)
        if left:
            garment=ImageOps.mirror(garment)
        overlay=Image.new("RGBA",image.size)
        overlay.alpha_composite(garment,(box[0],box[1]))
        mask=image.getchannel("A")
        # Keep dark foreground limbs, glasses, bamboo, and the peekaboo pillar.
        protect=Image.new("L",image.size)
        protected=[]
        props=[]
        for red,green,blue,alpha in image.getdata():
            dark=max(red,green,blue)<120 and not (lying or inverted)
            blue_prop=blue>red*1.10 and blue>green*.95
            bamboo=green>red*1.10 and green>blue*1.10
            saturated=max(red,green,blue)>=160 and max(red,green,blue)-min(red,green,blue)>90 and min(red,green,blue)<130
            pillar=key.startswith("scene_peekaboo") and red>green*1.15 and green>blue*1.3
            wood=key.startswith(("scene_log_","pack_sit_on_log_","pack_balance_on_log_")) and red>90 and red>green*1.15 and green>blue*1.3
            prop=blue_prop or bamboo or pillar or saturated or wood
            protected.append(255 if alpha>=128 and (dark or prop) else 0)
            props.append(255 if alpha>=128 and prop else 0)
        protect.putdata(protected)
        if key.startswith("pack_water_offer_"):
            index=int(key.rsplit("_",1)[1])
            glass={2:(117,100,137,129),3:(116,92,142,132),
                   4:(95,96,122,137),5:(87,96,121,138),
                   6:(76,96,115,141),7:(76,96,115,143)}.get(index)
            if glass:
                ImageDraw.Draw(protect).rectangle(glass,fill=255)
        if not lying and not inverted:
            # The central collar sits over the dark shoulder band; preserve
            # crossed foreground paws elsewhere.
            collar=ImageDraw.Draw(protect)
            collar.rectangle((l+3,max(0,hb-6),r-3,min(image.height-1,hb+8)), fill=0)
        prop_mask=Image.new("L",image.size)
        prop_mask.putdata(props)
        protect=ImageChops.lighter(protect,prop_mask)
        if key.startswith("pack_water_offer_") and glass:
            ImageDraw.Draw(protect).rectangle(glass,fill=255)
        mask=ImageChops.subtract(mask,protect)
        face_mask=Image.new("L",image.size)
        ImageDraw.Draw(face_mask).ellipse((hl,ht,hr,hb-3),fill=255)
        mask=ImageChops.subtract(mask,face_mask)
        overlay.putalpha(ImageChops.multiply(overlay.getchannel("A"),mask))
        out=Image.alpha_composite(out,overlay)
        cap=self.part(theme,"head_profile" if profile else "head_front")
        if key in ("scene_peekaboo_2","scene_peekaboo_4"):
            cap=None
        if cap is not None:
            cap_width=max(12,int((hr-hl)*(.60 if theme!="spooky" else 1.20)))
            if theme=="spooky":
                cap_height=max(12,int((hb-ht)*1.20))
                cap_top=ht-4
            else:
                cap_height=max(10,round(cap_width*cap.height/cap.width))
                cap_top=max(2,ht-int(cap_height*.50))
            cap=cap.resize((cap_width,cap_height),Image.Resampling.LANCZOS)
            if left:
                cap=ImageOps.mirror(cap)
            cap_layer=Image.new("RGBA",image.size)
            cap_layer.alpha_composite(cap,(int((hl+hr-cap_width)/2),cap_top))
            if theme=="spooky":
                face=Image.new("L",image.size)
                face_draw=ImageDraw.Draw(face)
                if profile:
                    face_draw.ellipse((hl-8 if left else hl+int((hr-hl)*.20),
                                       ht+int((hb-ht)*.14),
                                       hr-int((hr-hl)*.20) if left else hr+8,hb+2),fill=255)
                else:
                    face_draw.ellipse((hl+int((hr-hl)*.14),ht+int((hb-ht)*.24),hr-int((hr-hl)*.14),hb-3),fill=255)
                cap_layer.putalpha(ImageChops.subtract(cap_layer.getchannel("A"),face))
            out=Image.alpha_composite(out,cap_layer)
        out.putalpha(out.getchannel("A").point(lambda a:255 if a>=128 else 0))
        return out
