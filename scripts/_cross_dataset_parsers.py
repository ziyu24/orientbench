"""Shared cross-dataset OBB GT parsers (022/024)."""
import xml.etree.ElementTree as ET

def poly_to_obb(poly):
    import torch
    from mmrotate.structures.bbox import QuadriBoxes
    q = QuadriBoxes(torch.tensor([poly], dtype=torch.float32))
    return q.convert_to("rbox").tensor[0].tolist()

def parse_dior(xml_path):
    out = []
    try: root = ET.parse(xml_path).getroot()
    except Exception: return out
    for obj in root.findall("object"):
        rb = obj.find("robndbox"); name = obj.findtext("name", "object")
        if rb is None: continue
        try:
            poly = [float(rb.findtext(k)) for k in ("x_left_top","y_left_top","x_right_top","y_right_top",
                    "x_right_bottom","y_right_bottom","x_left_bottom","y_left_bottom")]
        except (TypeError, ValueError): continue
        out.append((poly, name))
    return out

def parse_fair1m(xml_path):
    out = []
    try: root = ET.parse(xml_path).getroot()
    except Exception: return out
    objs = root.find("objects")
    if objs is None: return out
    for obj in objs.findall("object"):
        name = obj.findtext("possibleresult/name") or "object"
        pts = obj.find("points")
        if pts is None: continue
        coords = []
        for pt in pts.findall("point"):
            x, y = pt.text.split(","); coords += [float(x), float(y)]
        if len(coords) >= 8: out.append((coords[:8], name))
    return out

def parse_dota_txt(txt_path):
    out = []
    for line in open(txt_path):
        p = line.split()
        if len(p) >= 9:
            try: poly = [float(x) for x in p[:8]]
            except ValueError: continue
            out.append((poly, p[8]))
    return out
