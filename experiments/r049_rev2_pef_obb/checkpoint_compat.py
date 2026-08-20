"""Late legacy-checkpoint compatibility, imported after torch by MMEngine."""
import sys
import numpy as np

# PSC checkpoints from the source host serialised these objects under the
# NumPy-2 module name.  Register aliases only after torch has imported NumPy;
# doing it during interpreter startup is unsafe in this NumPy-1.24 runtime.
sys.modules.setdefault('numpy._core', np.core)
sys.modules.setdefault('numpy._core.multiarray', np.core.multiarray)
sys.modules.setdefault('numpy._core.numeric', np.core.numeric)
