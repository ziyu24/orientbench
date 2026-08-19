"""Image-only HRSC dataset for post-seal T_cal/T_audit detector inference.

It reads only an allow-listed ID text file and never opens an annotation XML.
"""
import os.path as osp
from mmrotate.registry import DATASETS
from mmdet.datasets import BaseDetDataset

@DATASETS.register_module()
class R047ImageOnlyHRSC(BaseDetDataset):
    def load_data_list(self):
        ids=[x.strip() for x in open(self.ann_file) if x.strip()]
        return [{'img_id':i,'img_path':osp.join(self.data_root,f'{i}.bmp'),
                 'height':0,'width':0,'instances':[]}
                for i in ids]
