"""Checkpoint-only NumPy module-path compatibility for legacy PSC weights."""
import sys
import numpy as np

if not hasattr(np, '_core'):
    np._core = np.core
sys.modules.setdefault('numpy._core', np.core)
sys.modules.setdefault('numpy._core.multiarray', np.core.multiarray)
sys.modules.setdefault('numpy._core.numeric', np.core.numeric)
