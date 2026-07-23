"""Round-trip + interface unit test gate for the project-local DCLCoder.
DCL enters the R1 queue ONLY if this exits 0."""
import math, sys
import torch
from orientbench_ext.dcl_coder import DCLCoder
from mmrotate.registry import TASK_UTILS


def main():
    # 1) registered in mmrotate TASK_UTILS
    assert "DCLCoder" in TASK_UTILS.module_dict, "DCLCoder not registered"
    c = TASK_UTILS.build(dict(type="DCLCoder", angle_version="le90", omega=1))
    print(f"encode_size={c.encode_size} num_bins={c.num_bins}")
    assert c.encode_size == 8, c.encode_size  # ceil(log2(180)) = 8

    # 2) round-trip: decode(encode(theta)) within omega/2 (bin quantisation) for le90 range
    #    le90 angle range is [-pi/2, pi/2). Sample densely, exclude the top bin edge.
    thetas = torch.linspace(-math.pi/2 + 1e-4, math.pi/2 - 1e-3, 4000).unsqueeze(1)
    enc = c.encode(thetas)
    assert enc.shape == (4000, 8), enc.shape
    assert set(enc.unique().tolist()) <= {0.0, 1.0}, "encode not binary"
    # encode outputs {0,1}; decode thresholds at >0, so map 0->negative logit
    logits = enc * 2.0 - 1.0            # {0,1} -> {-1,+1}
    dec = c.decode(logits, keepdim=True)
    quant = math.radians(c.omega)       # one-bin tolerance
    err = (dec - thetas).abs()
    max_err = err.max().item()
    print(f"roundtrip max_err={math.degrees(max_err):.4f} deg (tol={c.omega} deg bin)")
    assert max_err <= quant + 1e-6, f"roundtrip error {math.degrees(max_err)} deg > {c.omega} deg"

    # 3) empty-input contract (mirrors CSLCoder)
    e = c.decode(torch.zeros(0, 8), keepdim=True)
    assert e.shape == (0, 1), e.shape
    e2 = c.decode(torch.zeros(0, 8), keepdim=False)
    assert e2.shape == (0,), e2.shape

    # 4) monotone-ish sanity: smallest angle -> low index bits, largest -> high
    lo = c.decode(c.encode(torch.tensor([[-math.pi/2 + 1e-3]])) * 2 - 1, keepdim=True)
    hi = c.decode(c.encode(torch.tensor([[math.pi/2 - 1e-2]])) * 2 - 1, keepdim=True)
    assert hi.item() > lo.item(), (lo.item(), hi.item())
    print("ALL DCLCoder UNIT TESTS PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
