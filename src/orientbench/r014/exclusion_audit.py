"""Read the two excluded calibration objects and state their original geometric exclusion."""
from __future__ import annotations
import argparse,json,math
from pathlib import Path
from shapely.geometry import Polygon
import tifffile

def main():
 p=argparse.ArgumentParser();p.add_argument('--dataset',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
 if a.out.exists():raise RuntimeError('exclusion audit output exists')
 fs=json.load(open(a.dataset/'real/metadata_annotations/RarePlanes_Public_All_Annotations.geojson'))['features'];out=[]
 for oid in (9082,10788):
  props=fs[oid]['properties'];name=f"{props['loc_id']}_{props['cat_id']}.tif";path=a.dataset/'real/imagery/train/PS-RGB_cog'/name
  if not path.exists():path=a.dataset/'real/imagery/calibration/PS-RGB_cog'/name
  with tifffile.TiffFile(path) as image:
   page=image.pages[0];scale=page.tags['ModelPixelScaleTag'].value;tie=page.tags['ModelTiepointTag'].value;w,h=page.imagewidth,page.imagelength
  pts=[((float(x)-float(tie[3]))/float(scale[0]),(float(tie[4])-float(y))/float(scale[1])) for x,y in fs[oid]['geometry']['coordinates'][0]]
  rect=Polygon(pts).minimum_rotated_rectangle;vertices=list(rect.exterior.coords)[:-1];edges=[math.dist(vertices[i],vertices[(i+1)%4]) for i in range(4)];side=math.ceil(1.25*math.hypot(max(edges),min(edges)));cx,cy=rect.centroid.coords[0];complete=cx-side/2>=0 and cy-side/2>=0 and cx+side/2<=w and cy+side/2<=h
  out.append({'object_id':oid,'loc_id':props['loc_id'],'cat_id':props['cat_id'],'source_cog':path.stem,'canvas_side':side,'center':[cx,cy],'image_width':w,'image_height':h,'complete_canvas':complete,'eligibility_reason':'incomplete_canvas_out_of_bounds' if not complete else 'unexpected_non_geometric_exclusion'})
 a.out.parent.mkdir(parents=True,exist_ok=True);a.out.write_text(json.dumps({'protocol':'r014-exclusion-audit-v1','test_opened':False,'model_forward':False,'records':out},sort_keys=True,indent=2)+'\n')
if __name__=='__main__':main()
