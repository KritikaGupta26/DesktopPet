"""Extract generated extension art; preserve all existing character frames.

Build-time only: Pillow, NumPy and SciPy. No runtime dependency is added.
"""
from pathlib import Path
import json
import shutil
import sys
import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage

ROOT = Path(__file__).resolve().parents[1]
FAMILIES = {
    'noodles': [0, 1], 'dumpling_balance': [2], 'dumpling_catch': [3],
    'belly_rub': [4], 'doodle': [5, 6], 'sneak': [7],
    'staff_ready': [8], 'staff_turn': [9], 'butterfly': [10, 11],
    'shadow_look': [12], 'startled': [13], 'hero_landing': [14], 'bashful': [15],
}
# Reviewed polygons in the 1254px generated source. Only foreground props,
# never paws, may reappear through a closed ghost sheet.
PROPS = {
    0: [[(122,211),(212,211),(206,257),(131,258)],[(143,174),(177,174),(177,222),(143,222)],[(54,164),(161,173),(160,185),(54,176)]],
    1: [[(410,222),(500,222),(494,266),(419,266)],[(469,165),(488,165),(488,200),(469,200)]],
    2: [[(769,100),(813,100),(813,150),(769,150)]],
    3: [[(1072,176),(1134,176),(1134,236),(1072,236)]],
    5: [[(386,547),(598,537),(609,611),(381,615)],[(387,478),(401,474),(443,574),(430,579)]],
    6: [[(718,474),(901,443),(899,590),(741,617)]],
    8: [[(20,707),(34,701),(290,901),(281,914)]],
    9: [[(330,774),(662,797),(660,826),(329,800)]],
    10: [[(847,627),(921,627),(921,704),(847,704)]],
    11: [[(1154,646),(1211,646),(1211,716),(1154,716)]],
}


def integrate(source):
    im = Image.open(source).convert('RGBA')
    data = np.array(im)
    labels, count = ndimage.label(data[:, :, 3] >= 128)
    objects = ndimage.find_objects(labels)
    sizes = np.bincount(labels.ravel())
    main = {}
    for label, box in enumerate(objects, 1):
        if box is None or sizes[label] < 3000:
            continue
        y, x = box
        row = min(3, int((y.start + y.stop) / 2 / im.height * 4))
        col = min(3, int((x.start + x.stop) / 2 / im.width * 4))
        index = row * 4 + col
        if index in main:
            raise ValueError('Two bodies occupy one sprite cell')
        main[index] = (label, box)
    if set(main) != set(range(16)):
        raise ValueError(f'Expected sixteen full bodies, got {sorted(main)}')
    frames = []
    props = []
    for index in range(16):
        label, (ys, xs) = main[index]
        mask = labels == label
        # Detached props (butterflies, chopstick ends) remain with the nearest
        # body. Tiny alpha speckles never become part of a runtime sprite.
        for extra, box in enumerate(objects, 1):
            if box is None or sizes[extra] < 40 or sizes[extra] >= 3000:
                continue
            y, x = box
            distances = {}
            for slot, (_, (my, mx)) in main.items():
                dx = max(0, mx.start-x.stop, x.start-mx.stop)
                dy = max(0, my.start-y.stop, y.start-my.stop)
                distances[slot] = dx*dx + dy*dy
            if min(distances, key=distances.get) == index and distances[index] < 55**2:
                mask |= labels == extra
        rgba = data.copy()
        rgba[:, :, 3] = np.where(mask, 255, 0).astype('uint8')
        cut = Image.fromarray(rgba)
        box = cut.getchannel('A').getbbox()
        cut = cut.crop(box)
        # Preserve a full silhouette and props; no rectangular edge clipping.
        scale=min(456/cut.width,450/cut.height)
        cut=cut.resize((round(cut.width*scale),round(cut.height*scale)),Image.Resampling.LANCZOS)
        canvas = Image.new('RGBA', (512, 512))
        canvas.alpha_composite(cut, ((512-cut.width)//2, 489-cut.height))
        frames.append(canvas)
        prop=Image.new('L',im.size)
        for polygon in PROPS.get(index,[]):
            ImageDraw.Draw(prop).polygon(polygon,fill=255)
        values=np.array(prop)
        # Dark paws in front of a bowl/scroll remain covered by the ghost.
        values=np.where((data[:,:,:3].max(axis=2)>130)&mask,values,0).astype('uint8')
        prop=Image.fromarray(values).crop(box).resize(cut.size,Image.Resampling.LANCZOS)
        aligned=Image.new('L',(512,512))
        aligned.paste(prop,((512-cut.width)//2,489-cut.height))
        props.append(aligned)
    manifest_path = ROOT/'assets/sprite_collection_manifest.json'
    manifest = json.loads(manifest_path.read_text())
    for family, indices in FAMILIES.items():
        for frame, index in enumerate(indices):
            frames[index].save(ROOT/f'assets/pack_{family}_{frame}.png')
            props[index].save(ROOT/f'assets/prop_{family}_{frame}.png')
        manifest[family] = {
            'sheet': 'artwork/v38/cute_extensions.png',
            'frames': len(indices), 'seconds_per_frame': 1.1,
            'mode': 'loop', 'label': family.replace('_', ' ').title(),
            'edge_only': False, 'generated_source': 'artwork/v38/cute_extensions.png',
            'source_cells': indices,
        }
    manifest_path.write_text(json.dumps(manifest, indent=2)+'\n')
    dest = ROOT/'artwork/v38'
    dest.mkdir(exist_ok=True)
    shutil.copy2(source, dest/'cute_extensions.png')
    print(f'Integrated {len(frames)} new poses; existing sprites untouched.')


if __name__ == '__main__':
    integrate(Path(sys.argv[1]))
