"""HRSC train/val-only real directed-heading data contract for r048."""
import math
import xml.etree.ElementTree as ET
from pathlib import Path
import cv2
import numpy as np
import torch
from torch.utils.data import Dataset

DATA = Path('/home/rspip/cqc/data/dataset/HRSC2016')
MEAN = torch.tensor([123.675, 116.28, 103.53]).view(3, 1, 1)
STD = torch.tensor([58.395, 57.12, 57.375]).view(3, 1, 1)

def wrap(x): return (x + math.pi) % (2 * math.pi) - math.pi
def axial_wrap(x): return (x + math.pi / 2) % math.pi - math.pi / 2

def records(split):
    """Never call this on audit: XML header semantics are only consumed for train/val."""
    if split not in {'train', 'val'}:
        raise ValueError('r048 contract permits only official train/val before G1 pass')
    out = []
    for iid in (DATA / 'splits' / f'{split}.txt').read_text().split():
        for j, obj in enumerate(ET.parse(DATA / 'annfiles' / f'{iid}.xml').getroot().findall('HRSC_Objects/HRSC_Object')):
            f = lambda k: float(obj.find(k).text)
            cx, cy, w, h, axis, hx, hy = [f(k) for k in ('mbox_cx', 'mbox_cy', 'mbox_w', 'mbox_h', 'mbox_ang', 'header_x', 'header_y')]
            if h > w:
                w, h, axis = h, w, axis + math.pi / 2
            axis = wrap(axis)
            dx, dy = hx - cx, hy - cy
            dist = math.hypot(dx, dy)
            if dist < .1 * w:
                continue
            phi = math.atan2(dy, dx)
            rel = wrap(phi - axis)
            # True centre-to-header vector, normalised by long side and represented
            # in the rectified crop coordinates so it is a learnable geometric target.
            vec = (dist / w * math.cos(rel), dist / w * math.sin(rel))
            out.append((iid, j, cx, cy, w, h, axis, phi, rel, *vec))
    return out

def render(r, rotation=0, axis_jitter=0):
    iid, _, cx, cy, w, h, axis, phi, rel, vx, vy = r
    render_axis = axis + math.radians(axis_jitter)
    image = cv2.imread(str(DATA / 'images' / f'{iid}.bmp'))
    mat = cv2.getRotationMatrix2D((cx, cy), math.degrees(render_axis), 1)
    mat[0, 2] += 96 - cx
    mat[1, 2] += 32 - cy
    crop = cv2.warpAffine(image, mat, (192, 64), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
    # The physical heading and OBB axis are expressed in the rendered coordinate
    # system; jitter is an inference-only axis reference perturbation.
    local = wrap(rel - math.radians(axis_jitter))
    if rotation:
        crop = cv2.rotate(crop, {90: cv2.ROTATE_90_CLOCKWISE, 180: cv2.ROTATE_180, 270: cv2.ROTATE_90_COUNTERCLOCKWISE}[rotation])
        crop = cv2.resize(crop, (192, 64), interpolation=cv2.INTER_LINEAR)
        local = wrap(local + math.radians(rotation))
    vnorm = math.hypot(vx, vy)
    vector = (vnorm * math.cos(local), vnorm * math.sin(local))
    crop = torch.from_numpy(cv2.cvtColor(crop, cv2.COLOR_BGR2RGB).copy()).permute(2, 0, 1).float()
    crop = (crop - MEAN) / STD
    # phi, local heading, real normalized vector, and the reference axis needed
    # to map model output back to global heading.
    target = torch.tensor([phi, local, vector[0], vector[1], wrap(render_axis)], dtype=torch.float32)
    return crop[:, :, :64], crop[:, :, 128:], crop, target

class HeadingDS(Dataset):
    def __init__(self, rows, aug=False, jitter=0):
        self.rows, self.aug, self.jitter = rows, aug, jitter
    def __len__(self): return len(self.rows)
    def __getitem__(self, index):
        rot = [0, 90, 180, 270][np.random.randint(4)] if self.aug else 0
        a, b, g, t = render(self.rows[index], 0, self.jitter)
        aa, bb, gg, tt = render(self.rows[index], rot, self.jitter)
        return a, b, g, t, aa, bb, gg, tt, rot
