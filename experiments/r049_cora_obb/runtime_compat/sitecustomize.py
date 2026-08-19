"""Checkpoint-only NumPy module-path compatibility for legacy PSC weights.

This changes no package version or runtime model code.  Some valid historic
weights serialised NumPy objects under ``numpy._core`` while the selected
pcp-obb environment exposes the compatible implementation as ``numpy.core``.
"""
import sys
import numpy as np

if not hasattr(np, '_core'):
    np._core = np.core
sys.modules.setdefault('numpy._core', np.core)
sys.modules.setdefault('numpy._core.multiarray', np.core.multiarray)
sys.modules.setdefault('numpy._core.numeric', np.core.numeric)
