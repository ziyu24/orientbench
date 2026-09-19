"""Real rotated-box counterexamples against the installed standard evaluator."""
import numpy as np
from orientbench.r029.run import build_oracle


def annotation(gt=(), ignored=()):
    gt = np.asarray(gt, np.float32).reshape(-1, 5)
    ignored = np.asarray(ignored, np.float32).reshape(-1, 5)
    return dict(bboxes=gt, labels=np.zeros(len(gt), np.int64), bboxes_ignore=ignored,
                labels_ignore=np.zeros(len(ignored), np.int64))


def verify():
    box = [0, 0, 10, 2, 0]
    # Many equal scores, deliberately interleaved FP/TP; global quicksort is not stable.
    d1 = np.array([[30 if i % 3 else 0, 0, 10, 2, 0, .5] for i in range(20)], np.float32)
    d2 = d1[::-1].copy()
    build_oracle([d1, d2, np.empty((0, 6), np.float32)],
                 [annotation([box]), annotation([box], [[30, 0, 10, 2, 0]]), annotation()], .5)
    # Actual IoU crosses .5 while only one GT exists.
    det = np.array([[0, 0, 10, 2, 0, .9]], np.float32)
    _, first, _ = build_oracle([det], [annotation([box])], .5)
    _, second, _ = build_oracle([det], [annotation([[4, 0, 10, 2, 0]])], .5)
    assert first == 1 and second == 0
    # r028 matching-switch geometry: no alternate-unoccupied matching allowed.
    det = np.array([[1, 0, 10, 2, 0, .9], [0, 0, 10, 2, 0, .8]], np.float32)
    _, first, _ = build_oracle([det], [annotation([[-.01, 0, 10, 2, 0], [2, 0, 10, 2, 0]])], .5)
    _, second, _ = build_oracle([det], [annotation([[.01, 0, 10, 2, 0], [2, 0, 10, 2, 0]])], .5)
    assert first != second
    print('r029 standard-evaluator counterexamples passed')


if __name__ == '__main__':
    verify()
