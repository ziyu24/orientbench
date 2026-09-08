"""Signed-camera ray intersections and image-only feasible-set inference."""
import numpy as np


def render_extra(scene, heights, action, ys):
    """Trace rays for a positive or negative camera slope; no oracle input."""
    heights = np.atleast_2d(heights)
    slope = action['slope']
    if not np.isfinite(slope) or slope == 0:
        raise ValueError('nonzero finite slope required')
    us = np.linspace(action['u_start'], action['u_stop'], action['u_count'])
    yy, uu = np.meshgrid(ys, us, indexing='ij')
    origin_x = uu.ravel() + slope * scene['camera_z']
    ymin, ymax = scene['box_y_bounds']
    inside_y = (yy.ravel() >= ymin) & (yy.ravel() <= ymax)
    half = scene['box_width'] / 2
    foreground = np.zeros((len(heights), uu.size), dtype=bool)
    for b, center in enumerate(scene['box_centers_x']):
        tx0 = (origin_x - center - half) / slope
        tx1 = (origin_x - center + half) / slope
        enter = np.maximum(np.minimum(tx0, tx1), scene['camera_z'] - heights[:, b, None])
        leave = np.minimum(np.maximum(tx0, tx1), scene['camera_z'])
        foreground |= (heights[:, b, None] > 0) & inside_y & (enter <= leave) & (leave >= 0)
    return np.where(foreground[..., None], scene['object_rgb'], scene['ground_rgb']).astype(
        np.uint8).reshape(len(heights), len(ys), len(us), 3)


def validate_view_support(scene, heights, targets, actions, ys, expected_samples):
    """Check all hypotheses, not only the selected true scene or visible points."""
    if max(np.max(heights), np.max(targets)) >= scene['camera_z']:
        raise ValueError('camera must be above all candidate surfaces')
    half = scene['box_width'] / 2
    for action in actions:
        if action['u_count'] * len(ys) != expected_samples:
            raise ValueError('unequal new ray sample budget')
        lo, hi, slope = action['u_start'], action['u_stop'], action['slope']
        if not lo < hi or action['u_count'] < 2:
            raise ValueError('invalid image grid')
        for q, (x, y) in enumerate(scene['queries_xy']):
            u = x - slope * targets[:, q]
            if np.any(u < lo) or np.any(u > hi) or not min(ys) <= y <= max(ys):
                raise ValueError('query outside camera field of view')
        for b, center in enumerate(scene['box_centers_x']):
            left = center - half - np.maximum(slope * heights[:, b], 0)
            right = center + half - np.minimum(slope * heights[:, b], 0)
            if np.any(left < lo) or np.any(right > hi):
                raise ValueError('candidate object support outside camera field of view')


def compatible_ids(base_images, base_observation, extra_images, extra_observation):
    """Exactly one new image; no scene ID, target, class, or visibility argument."""
    base = np.all(base_images == base_observation, axis=tuple(range(1, base_images.ndim)))
    extra = np.all(extra_images == extra_observation, axis=tuple(range(1, extra_images.ndim)))
    ids = np.flatnonzero(base & extra)
    if not len(ids):
        raise ValueError('empty image-compatible set')
    return ids.tolist()
