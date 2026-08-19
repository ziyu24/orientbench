"""MMRotate datasets which enumerate supplied image IDs and never parse GT."""
from pathlib import Path

try:
    from mmrotate.registry import DATASETS
    from mmdet.datasets import BaseDetDataset
    @DATASETS.register_module()
    class R045ImageOnlyDataset(BaseDetDataset):
        def load_data_list(self):
            ids=Path(self.ann_file).read_text().splitlines()
            return [dict(img_id=i,img_path=str(Path(self.data_root)/f'{i}.bmp'),height=0,width=0,instances=[]) for i in ids]
except ImportError:
    pass

try:
    from mmrotate.datasets.builder import ROTATED_DATASETS
    from mmdet.datasets import CustomDataset
    @ROTATED_DATASETS.register_module()
    class R045LegacyImageOnlyDataset(CustomDataset):
        CLASSES=('ship',)
        def load_annotations(self, ann_file):
            return [dict(filename=f'{i}.bmp',width=0,height=0,ann=dict(bboxes=[],labels=[])) for i in Path(ann_file).read_text().splitlines()]
except ImportError:
    pass
