"""Numerically equivalent weighted normal-equation implementation for r005 CPU audit."""
from __future__ import annotations
import math
import cv2
import numpy as np
from orientbench.r004.observability import Observable, circular_crop, fixed_noise_scale


def _coef(columns, target, weight):
    good = weight.ravel() > 0
    a = columns.reshape(-1, columns.shape[-1])[good]
    y = target.ravel()[good]
    w = weight.ravel()[good]
    gram = a.T @ (a * w[:, None])
    rhs = a.T @ (w * y)
    return np.linalg.pinv(gram, rcond=1e-12) @ rhs, a, y, w


def _alias_margin(patch, weight, sigma0):
    height, width = patch.shape; center = ((width - 1) / 2, (height - 1) / 2)
    yy, xx = np.mgrid[:height, :width].astype(np.float64)
    denom = sigma0 * sigma0 * float(weight.sum()); errors = []
    for degrees in range(15, 180, 5):
        matrix = cv2.getRotationMatrix2D(center, float(degrees), 1.0)
        rotated = cv2.warpAffine(patch.astype(np.float32), matrix, (width, height), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT_101).astype(np.float64)
        gx = cv2.Sobel(rotated, cv2.CV_64F, 1, 0, ksize=3); gy = cv2.Sobel(rotated, cv2.CV_64F, 0, 1, ksize=3)
        columns = np.stack([gx, gy, (xx-center[0])*gx + (yy-center[1])*gy, rotated, np.ones_like(rotated)], -1)
        coefficient, a, y, w = _coef(columns, patch, weight); coefficient[3] = max(0.0, coefficient[3])
        errors.append(float(np.sum(w * (y - a @ coefficient) ** 2) / denom))
    return max(0.0, min(errors) if errors else 0.0)


def measure(patch, weight, sigma0):
    image = patch.astype(np.float64); gx = cv2.Sobel(image, cv2.CV_64F, 1, 0, ksize=3); gy = cv2.Sobel(image, cv2.CV_64F, 0, 1, ksize=3)
    height, width = image.shape; yy, xx = np.mgrid[:height, :width].astype(np.float64); x, y = xx-(width-1)/2, yy-(height-1)/2
    gtheta = -y*gx+x*gy; columns = np.stack([gx, gy, x*gx+y*gy, image, np.ones_like(image)], -1)
    coefficient, a, target, w = _coef(columns, gtheta, weight)
    residual = target-a@coefficient
    j = float(np.sum(w*residual**2)/(sigma0*sigma0*weight.sum()))
    aa=float(np.sum(weight*gx*gx)); b=float(np.sum(weight*gx*gy)); c=float(np.sum(weight*gy*gy))
    coherence=((aa-c)**2+4*b*b)/max((aa+c)**2,1e-12); grad=(aa+c)/max(weight.sum(),1.)
    edge=float(np.sum(weight*(np.hypot(gx,gy)>np.percentile(np.hypot(gx,gy)[weight>0],75)))/weight.sum())
    return Observable(j, _alias_margin(image,weight,sigma0), float(np.sum(weight*gtheta*gtheta)/(sigma0*sigma0*weight.sum())), float(coherence),float(grad),edge,float(np.sqrt(np.average((image-np.average(image,weights=weight))**2,weights=weight))),float(weight.sum()))
