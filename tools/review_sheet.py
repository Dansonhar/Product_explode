"""Create a review contact sheet from the newly rendered 3D models."""
import json
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
root=Path(__file__).resolve().parents[1]
catalog=json.loads((root/'viewer/public/models/catalog.json').read_text())
font=ImageFont.truetype('/System/Library/Fonts/Helvetica.ttc',20)
small=ImageFont.truetype('/System/Library/Fonts/Helvetica.ttc',13)
for start in range(0,len(catalog),12):
 products=catalog[start:start+12];sheet=Image.new('RGB',(1600,((len(products)+3)//4)*350),(241,244,247));d=ImageDraw.Draw(sheet)
 for i,p in enumerate(products):
  x=(i%4)*400;y=(i//4)*350;im=Image.open(root/'viewer/public/renders'/p['variants'][0]['render']).convert('RGB');im.thumbnail((390,300));sheet.paste(im,(x+(400-im.width)//2,y+5));d.text((x+12,y+304),p['name'],fill=(27,40,53),font=font);d.text((x+12,y+331),'Photo '+p['photo']+' · reconstructed study',fill=(98,110,123),font=small)
 sheet.save(root/f'viewer/public/renders/review-{start//12+1}.jpg',quality=94)
