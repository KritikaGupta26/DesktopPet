"""Finite playful routines and a real reflection of the currently dressed pose."""
from PIL import Image, ImageChops, ImageDraw, ImageOps
from scene_playback import scene_pose

MIRROR_TIMELINE = ((0,1.0),(1,1.1),(2,1.0),(3,.6),(4,1.0),(5,1.1),(6,1.3),(7,1.4))
MIRROR_DURATION = sum(seconds for _,seconds in MIRROR_TIMELINE)
BOO_DURATION = 5.5
PRANK_COOLDOWN_MINUTES = 15

def mirror_pose(elapsed):
    return scene_pose({'timeline':MIRROR_TIMELINE},elapsed)

def reflected_pose(image):
    return ImageOps.mirror(image).resize((104,104),Image.Resampling.LANCZOS)

def compose_mirror(image, mirror):
    """Use the SAME themed pose on both sides, with the reflection inside glass."""
    out=Image.new('RGBA',(360,180))
    out.alpha_composite(mirror,(215,1))
    reflection=Image.new('RGBA',out.size)
    reflection.alpha_composite(reflected_pose(image),(230,38))
    glass=Image.new('L',out.size)
    ImageDraw.Draw(glass).ellipse((236,20,328,153),fill=225)
    reflection.putalpha(ImageChops.multiply(reflection.getchannel('A'),glass))
    out=Image.alpha_composite(out,reflection)
    out.alpha_composite(image,(0,0))
    out.putalpha(out.getchannel('A').point(lambda a:255 if a>=128 else 0))
    return out

def boo_phase(elapsed):
    if elapsed<.55:return 0,'pack_happy_idle_5','Shh… I have a tiny surprise.'
    if elapsed<1.45:return 1,'pack_jump_2','Boo!'
    if elapsed<2.65:return 2,'pack_mirror_4','Oops… I scared myself.'
    return 3,'pack_mirror_7','Just kidding. Your fluffy friend!'
