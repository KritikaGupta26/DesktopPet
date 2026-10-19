"""Fit shaded costume components to each animated body, preserving foreground paws."""
from collections import OrderedDict
import math
from ghost_cloak import dress_ghost
from PIL import Image, ImageChops, ImageDraw, ImageOps


# Reviewed source coordinates: inner linings belong behind the panda, not on
# top of its face/chest. Coordinates are fractions of each original cutout.
REAR_SURFACES = {
    ("navratri", "front"): ((.29,.04),(.71,.04),(.59,.97),(.43,.97)),
    ("navratri", "profile"): ((.26,.24),(.48,.20),(.61,.30),(.62,.49),(.53,.61),(.33,.58),(.23,.44)),
    ("diwali", "front"): ((.29,.01),(.72,.01),(.64,.065),(.40,.065)),
    ("diwali", "profile"): ((.25,.01),(.61,.01),(.54,.06),(.32,.06)),
    ("holi", "front"): ((.30,.01),(.70,.01),(.61,.07),(.41,.07)),
    ("krishna", "front"): ((.29,.02),(.71,.02),(.54,.35),(.46,.35)),
    ("krishna", "profile"): ((.11,.22),(.25,.18),(.37,.26),(.39,.42),(.28,.55),(.13,.49),(.07,.35)),
    ("new_year", "front"): ((.30,.01),(.71,.01),(.62,.095),(.40,.095)),
    ("new_year", "profile"): ((.12,.25),(.26,.22),(.39,.33),(.40,.46),(.30,.59),(.14,.53),(.08,.39)),
    ("ganesh", "front"): ((.31,.015),(.70,.015),(.58,.13),(.41,.13)),
    ("ganesh", "profile"): ((.12,.21),(.26,.18),(.38,.27),(.39,.42),(.28,.54),(.13,.48),(.07,.34)),
    ("navratri", "head_profile"): ((.70,.67),(.98,.64),(.92,.99),(.76,.91)),
}


def front_surface(part, theme, name):
    """Remove occluded rear source surfaces before fitting, without repainting."""
    polygon = REAR_SURFACES.get((theme, name))
    if not polygon:
        return part
    out = part.copy()
    mask = out.getchannel("A")
    ImageDraw.Draw(mask).polygon([(round(x*part.width), round(y*part.height)) for x,y in polygon], fill=0)
    out.putalpha(mask)
    return out


def headgear_geometry(head, torso, cap_size, theme, key):
    """Fit a crown to the local head axis and rotate it with the whole pose."""
    hl,ht,hr,hb = head
    l,t,r,b = torso
    cx,cy = (hl+hr)/2, (ht+hb)/2
    tx,ty = (l+r)/2, (t+b)/2
    # Ordinary head tilts are small. Large rotations are reserved for poses
    # whose torso is sideways or above the head.
    sideways = key.startswith(("pack_sleep_", "pack_snore_sleep_")) or key in ("pack_sploot_2", "pack_sploot_3", "pack_wake_up_0", "pack_wake_up_1")
    inverted = key in ("pack_forward_roll_2", "pack_forward_roll_3", "pack_forward_roll_4", "pack_forward_roll_6", "pack_sploot_0", "pack_sploot_1")
    angle = math.degrees(math.atan2(tx-cx, ty-cy)) if sideways or inverted else max(-16, min(16, math.degrees(math.atan2(tx-cx, max(1,ty-cy)))))
    # These sleep drawings roll the torso onto its side while keeping the
    # face almost upright. Using the body axis would put a hat on its cheek.
    if key.startswith("pack_snore_sleep_"):
        angle = -36
    elif key.startswith("pack_sleep_") or key in ("pack_wake_up_0", "pack_wake_up_1"):
        angle = -12
    radians = math.radians(angle)
    cross = abs(math.cos(radians))*(hr-hl)+abs(math.sin(radians))*(hb-ht)
    depth = abs(math.cos(radians))*(hb-ht)+abs(math.sin(radians))*(hr-hl)
    ratio = {"navratri": .82, "krishna": .60, "christmas": .82, "summer": 1.02, "winter": .88, "birthday": .46, "new_year": .46}.get(theme, .80)
    width = max(12, round(cross*ratio))
    height = max(10, round(width*cap_size[1]/cap_size[0]))
    # Preserve source proportions, but keep tall crowns inside the pose canvas.
    max_height = depth*(.85 if theme in ("birthday", "new_year") else .78)
    if height > max_height:
        width = max(12, round(width*max_height/height))
        height = max(10, round(max_height))
    # The lower rim fits the forehead, rather than floating above the head.
    anchor = (cx-math.sin(radians)*depth*.20, cy-math.cos(radians)*depth*.20)
    return width, height, angle, anchor


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
        "pack_wake_up_1":((44,112,115,166),(112,124,149,168)),
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
    # A visible cream patch is not a body boundary. Crossed paws, a bamboo
    # stalk or a near leg can split that patch into tiny disconnected islands.
    # Fit to the anatomical torso, then retain foreground limbs separately.
    if key.startswith(("pack_walk_", "pack_run_", "pack_bored_shuffle_")):
        torso=(int((head[0]+head[2])/2-30),head[3]+5,
               int((head[0]+head[2])/2+30),min(158,opaque[3]-16))
    elif key.startswith(("pack_walk_left_", "pack_run_left_", "pack_bored_shuffle_left_")):
        torso=(int((head[0]+head[2])/2-30),head[3]+5,
               int((head[0]+head[2])/2+30),min(158,opaque[3]-16))
    if key.startswith(("pack_eat_bamboo_", "pack_sit_down_", "pack_belly_scratch_",
                       "pack_noodles_", "pack_doodle_", "pack_belly_rub_")):
        torso=(head[0]+17,head[3]+4,head[2]-17,opaque[3]-6)
    if key.startswith("pack_staff_turn_"):
        # The pale staff motion arc is not part of the belly. Detecting it
        # as torso fabric painted a detached sleeve over empty space.
        width=head[2]-head[0]
        torso=(head[0]+round(width*.23),head[3]+3,
               head[2]-round(width*.23),opaque[3]-8)
    return head,torso,profile,key.startswith(("pack_walk_left", "pack_run_left", "pack_bored_shuffle_left"))


class Wardrobe:
    def __init__(self, assets):
        self.assets=assets
        self.parts={}
        self.geometry={}
        self.prop_masks={}
        self.cache=OrderedDict()

    def part(self, theme, name):
        cache_key=(theme,name)
        if cache_key not in self.parts:
            path=self.assets/f"wardrobe_{theme}_{name}.png"
            self.parts[cache_key]=front_surface(Image.open(path).convert("RGBA"), theme, name) if path.exists() else None
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
            out=dress_ghost(image, self.part(theme, "full_profile" if profile else "full_front"), geometry, key)
            if key in self.prop_masks:
                out.paste(image,(0,0),ImageChops.multiply(self.prop_masks[key].point(lambda a:255 if a>=128 else 0),image.getchannel('A')))
                out.putalpha(out.getchannel('A').point(lambda a:255 if a>=128 else 0))
            return out
        out=image.copy()
        l,t,r,b=torso
        hl,ht,hr,hb=head
        lying=key.startswith(("pack_sleep_","pack_snore_sleep_")) or key in ("pack_sploot_2","pack_sploot_3","pack_wake_up_0","pack_wake_up_1")
        name="profile" if profile or lying else "front"
        cloth=self.part(theme,name)
        if cloth is None:
            raise ValueError(f"Missing persistent outfit: {theme}/{name}")
        scarf=theme in ("autumn","thanksgiving","christmas","valentine","birthday","shiva","spring","summer","winter")
        inverted=key in ("pack_forward_roll_2","pack_forward_roll_3","pack_forward_roll_4","pack_forward_roll_6","pack_sploot_0","pack_sploot_1")
        if lying and scarf:
            # A scarf wraps the neck next to the resting cheek; it must not
            # turn into a stretched rectangular patch across the back.
            width=max(12,round((hr-hl)*.22))
            height=max(18,round((hb-ht)*.52))
            box=(hr-12,ht+round((hb-ht)*.35),hr-12+width,
                 ht+round((hb-ht)*.35)+height)
            cloth=cloth.rotate(78,expand=True)
        elif lying or inverted:
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
        seated = key.startswith(("pack_eat_bamboo_", "pack_belly_scratch_")) or key in ("pack_sit_down_2", "pack_sit_down_3")
        if seated:
            # Pale paw pads are neither dark fur nor a saturated prop. Keep
            # the entire foreground feet, including their highlighted pads.
            feet=ImageDraw.Draw(protect)
            ground=image.getchannel("A").getbbox()[3]
            feet.ellipse((hl-17,ground-34,l+8,ground+2),fill=255)
            feet.ellipse((r-8,ground-34,hr+17,ground+2),fill=255)
        glass=None
        if key.startswith(("pack_water_offer_", "pack_alternate_offer_", "pack_drink_water_")):
            # Locate water in the fitted image. Old pixel coordinates become
            # wrong as soon as the whole sequence is scaled or repositioned.
            water=Image.new("L",image.size)
            water.putdata([255 if a>=128 and blue>105 and blue>red*1.10 and blue>green*.95 else 0
                           for red,green,blue,a in image.getdata()])
            bounds=water.getbbox()
            if bounds:
                gl,gt,gr,gb=bounds
                glass=(max(0,gl-4),max(0,gt-12),min(image.width-1,gr+4),min(image.height-1,gb+3))
                ImageDraw.Draw(protect).rectangle(glass,fill=255)
        if not lying and not inverted:
            # The central collar sits over the dark shoulder band; preserve
            # crossed foreground paws elsewhere.
            collar=ImageDraw.Draw(protect)
            collar.rectangle((l+3,max(0,hb-3),r-3,min(image.height-1,hb+3)), fill=0)
        prop_mask=Image.new("L",image.size)
        prop_mask.putdata(props)
        protect=ImageChops.lighter(protect,prop_mask)
        if key in self.prop_masks:
            protect=ImageChops.lighter(protect,self.prop_masks[key])
        if glass:
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
            cap_width, cap_height, angle, anchor = headgear_geometry(head, torso, cap.size, theme, key)
            cap = cap.resize((cap_width, cap_height), Image.Resampling.LANCZOS)
            if left:
                cap = ImageOps.mirror(cap)
            # Rotate around the fitted lower rim, not the unrotated image centre.
            local = Image.new("RGBA", (cap_width*3, cap_height*3))
            local.alpha_composite(cap, (cap_width, round(cap_height*.5)))
            local = local.rotate(angle, resample=Image.Resampling.BICUBIC, expand=False)
            cap_layer = Image.new("RGBA", image.size)
            px = round(anchor[0]-local.width/2)
            py = round(anchor[1]-local.height/2)
            # In the default 180px canvas some jumping/gait crowns reach the
            # top edge. Keep the entire crown visible, never slice its crest.
            bounds = local.getchannel("A").getbbox()
            if bounds:
                px = max(2-bounds[0], min(px, image.width-2-bounds[2]))
                py = max(2-bounds[1], min(py, image.height-2-bounds[3]))
            cap_layer.alpha_composite(local, (px,py))
            # The forehead/eyes remain unobstructed underneath hollow hats.
            face = Image.new("L", image.size)
            ImageDraw.Draw(face).ellipse((hl+int((hr-hl)*.08), ht+int((hb-ht)*.33), hr-int((hr-hl)*.08), hb-2), fill=255)
            if not inverted:
                cap_layer.putalpha(ImageChops.subtract(cap_layer.getchannel("A"),face))
            out = Image.alpha_composite(out,cap_layer)
        if key in self.prop_masks:
            out.paste(image,(0,0),ImageChops.multiply(self.prop_masks[key].point(lambda a:255 if a>=128 else 0),image.getchannel('A')))
        out.putalpha(out.getchannel("A").point(lambda a:255 if a>=128 else 0))
        return out
