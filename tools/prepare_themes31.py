"""Extract generated seasonal props without inventing artwork or a background."""
from pathlib import Path
import sys
from PIL import Image
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from seasonal_themes import PROP_KEYS
with Image.open(ROOT/'artwork/season_props_v31_source.png') as opened:
    sheet=opened.convert('RGBA')
for i,key in enumerate(PROP_KEYS):
    col,row=i%4,i//4
    cell=sheet.crop((round(col*sheet.width/4),round(row*sheet.height/4),
                     round((col+1)*sheet.width/4),round((row+1)*sheet.height/4)))
    box=cell.getchannel('A').point(lambda a:255 if a>=128 else 0).getbbox()
    if not box:
        raise ValueError(f'Empty prop: {key}')
    cell=cell.crop(box)
    cell.thumbnail((224,224),Image.Resampling.LANCZOS)
    out=Image.new('RGBA',(256,256))
    out.alpha_composite(cell,((256-cell.width)//2,240-cell.height))
    out.save(ROOT/f'assets/theme_{key}.png')
print(f'Prepared {len(PROP_KEYS)} alpha props.')
