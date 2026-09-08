"""Exact finite scene family with sampled, unlit orthographic images.

All buildings have the same known RGB value. This deliberately measures
silhouette evidence, not textured stereo or a learned segmentation model.
"""
from itertools import product
import hashlib
import numpy as np


def catalog(cfg):
    return np.array(list(product(cfg['height_values'], repeat=len(cfg['box_centers_x']))), dtype=np.int16)


def image_grid(cfg):
    u = np.linspace(**dict(start=cfg['image_u']['start'], stop=cfg['image_u']['stop'], num=cfg['image_u']['count']))
    slopes, vv, uu = np.meshgrid(cfg['camera_slopes_x'], cfg['image_v'], u, indexing='ij')
    return slopes.ravel(), vv.ravel(), uu.ravel()


def render(cfg, heights):
    """Ray-box slab intersections, batched across scenes; RGB only is observed."""
    heights = np.atleast_2d(heights)
    slope, y, u = image_grid(cfg)
    z = cfg['camera_z']
    origin_x = u + slope*z
    nearest = np.full((len(heights), len(u)), np.inf)
    ymin, ymax = cfg['box_y_bounds']
    inside_y = (y >= ymin) & (y <= ymax)
    half = cfg['box_width']/2
    for b, x in enumerate(cfg['box_centers_x']):
        tx1, tx2 = (origin_x-x-half)/slope, (origin_x-x+half)/slope
        enter = np.maximum(tx1[None, :], z-heights[:, b, None])
        leave = np.minimum(tx2, z)
        hit = (heights[:, b, None] > 0) & inside_y & (enter <= leave) & (leave >= 0)
        nearest = np.minimum(nearest, np.where(hit, np.maximum(enter, 0), np.inf))
    rgb = np.where(np.isfinite(nearest)[..., None], cfg['object_rgb'], cfg['ground_rgb']).astype(np.uint8)
    return rgb.reshape(len(heights), len(cfg['camera_slopes_x']), len(cfg['image_v']), cfg['image_u']['count'], 3)


def query_geometry(cfg, heights):
    """Use each candidate's own highest surface, never a true-scene projection."""
    heights = np.atleast_2d(heights)
    targets = np.zeros((len(heights), len(cfg['queries_xy'])), dtype=np.int16)
    bits = np.zeros_like(targets, dtype=np.uint8)
    half = cfg['box_width']/2
    ymin, ymax = cfg['box_y_bounds']
    tol = cfg['ray_tolerance']
    for q, (x, y) in enumerate(cfg['queries_xy']):
        covering = [b for b, center in enumerate(cfg['box_centers_x']) if abs(x-center) <= half and ymin <= y <= ymax]
        if covering:
            targets[:, q] = heights[:, covering].max(axis=1)
        h = targets[:, q]
        for v, slope in enumerate(cfg['camera_slopes_x']):
            projected_u = x-slope*h
            if np.any(projected_u < cfg['image_u']['start']) or np.any(projected_u > cfg['image_u']['stop']) or not min(cfg['image_v']) <= y <= max(cfg['image_v']):
                raise ValueError('query outside camera field of view')
            blocked = np.zeros(len(heights), dtype=bool)
            if ymin <= y <= ymax:
                for b, center in enumerate(cfg['box_centers_x']):
                    # From (x,y,h), trace toward the camera with dz/dt=1.
                    enter = np.maximum((center-half-x)/slope, -h)
                    leave = np.minimum((center+half-x)/slope, heights[:, b]-h)
                    blocked |= (heights[:, b] > 0) & (leave >= np.maximum(enter, tol)) & (enter < cfg['camera_z']-h)
            bits[:, q] |= ((~blocked).astype(np.uint8) << v)
    return targets, bits


def prepare_manifest(cfg):
    """Geometry-only sampling. Does not render or evaluate feasible ranges."""
    heights = catalog(cfg)
    targets, bits = query_geometry(cfg, heights)
    q = cfg['stratum_query_index']
    pools = {name: [] for name in cfg['strata']}
    for i, (h, mask) in enumerate(zip(targets[:, q], bits[:, q])):
        if mask == 0:
            label = 'common_occluded'
        elif mask != 7:
            label = 'one_side_occluded'
        else:
            label = 'depth_boundary' if h >= cfg['boundary_height_min'] else 'unoccluded'
        pools[label].append(i)
    records = []
    for label in cfg['strata']:
        order = sorted(pools[label], key=lambda i: hashlib.sha256(f"{cfg['seed']}|{label}|{i}".encode()).hexdigest())
        if len(order) < cfg['scenes_per_stratum']:
            raise ValueError(f'insufficient geometry-only stratum: {label}')
        for i in order[:cfg['scenes_per_stratum']]:
            records.append({'catalog_id': i, 'heights': heights[i].tolist(), 'stratum': label})
    return {'task': cfg['task'], 'catalog_size': len(heights), 'pool_sizes': {k: len(v) for k, v in pools.items()}, 'records': records}


def infer(images, observation, targets, visibility, query, oracle_bits=None):
    """No true ID, target height, class or other-query oracle is accepted."""
    match = np.all(images == observation, axis=tuple(range(1, images.ndim)))
    if oracle_bits is not None:
        match &= visibility[:, query] == oracle_bits
    ids = np.flatnonzero(match)
    if not len(ids):
        raise ValueError('empty compatible scene set')
    vals = targets[ids, query]
    return ids.tolist(), int(vals.min()), int(vals.max())
