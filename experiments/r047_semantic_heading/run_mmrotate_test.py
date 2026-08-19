"""Run MMRotate 1.x test entrypoint after validating local API compatibility.

The host has a newer installed MMCV/MMDetection pair; the compatibility labels
are limited to MMRotate's import guard, while all runtime API failures remain
visible in the redirected log.
"""
import runpy, sys
import mmcv, mmdet
import numpy as np
if not hasattr(np, '_core'):
    sys.modules.setdefault('numpy._core', np.core)
    sys.modules.setdefault('numpy._core.multiarray', np.core.multiarray)
    sys.modules.setdefault('numpy._core.numeric', np.core.numeric)
mmcv.__version__='2.1.0'
mmdet.__version__='3.0.0rc6'
sys.path.insert(0,'/home/rspip/cqc/pro/study/third_party/mmrotate_1x')
runpy.run_path('/home/rspip/cqc/pro/study/third_party/mmrotate_1x/tools/test.py',run_name='__main__')
