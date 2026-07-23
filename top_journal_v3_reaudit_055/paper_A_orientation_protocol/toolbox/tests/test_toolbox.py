import csv,json,math,unittest
from pathlib import Path
import numpy as np
from orientation_reliability.core import *

class TestCore(unittest.TestCase):
    def test_circular(self): self.assertAlmostEqual(float(circular_distance_le90(179,1)),2)
    def test_nrc(self):
        r=np.array([0.,1.,2.,3.]);self.assertAlmostEqual(nrc(-r,r),0);self.assertGreater(nrc(r,r),1)
    def test_delta(self): self.assertGreater(delta_tau(2.1,.5),delta_tau(2.1,.75))
    def test_nonempty(self):
        q=conditional_scene_risk(['a','b'],[0,1],[1,0],['a','b']);self.assertEqual(q['nonempty_scenes'],1);self.assertEqual(q['nonempty_scene_rate'],.5)
    def test_infeasible_explicit(self): self.assertTrue(all(x['status']=='INFEASIBLE' for x in certify_alpha_frontier([1,2],[1,1],['a','b'])))
    def test_persistent_regression(self):
        root=Path(__file__).resolve().parents[4];p=root/'outputs/persistent_artifacts/m069_fullval_reliability/A/matched_fullval.jsonl';s=[];r=[]
        with p.open() as f:
            for i,line in enumerate(f):
                if i==2000:break
                x=json.loads(line)
                if float(x['aspect_ratio'])>=2.1:s.append(float(x['score']));r.append(float(x['angle_error']))
        self.assertGreater(len(s),100);self.assertTrue(math.isfinite(nrc(s,r)))
if __name__=='__main__':unittest.main()
