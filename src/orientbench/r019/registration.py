"""Integer translations on a fixed common interior; no padding or label warping."""
import numpy as np


def shifted_core(array, dy, dx, margin):
    a = np.asarray(array)
    if not all(isinstance(v, (int, np.integer)) for v in (dy, dx, margin)):
        raise ValueError("integer translations required")
    if a.ndim < 2 or margin < 1 or min(a.shape[-2:]) <= 2 * margin:
        raise ValueError("nonempty fixed interior required")
    if max(abs(dy), abs(dx)) > margin:
        raise ValueError("translation outside frozen search")
    h, w = a.shape[-2:]
    return a[..., margin + dy:h - margin + dy, margin + dx:w - margin + dx]


def check_support(target, valid, side=None):
    y, mask = np.asarray(target), np.asarray(valid)
    if y.ndim != 2 or y.shape != mask.shape or (side and y.shape != (side, side)):
        raise ValueError("wrong common grid")
    # All 384 existing tiles had complete support in r018. Do not silently change
    # the cohort or fit shift-dependent masks when that established fact changes.
    if not np.isin(y, [0, 1]).all() or mask.dtype != bool or not mask.all():
        raise ValueError("binary labels and previously verified full valid support required")


def _valid_correlation(image, template):
    """Linear convolution with a reversed template, restricted to valid offsets."""
    h, w = image.shape
    th, tw = template.shape
    shape = tuple(1 << (n - 1).bit_length() for n in (h + th - 1, w + tw - 1))
    full = np.fft.irfft2(np.fft.rfft2(image, s=shape) *
                         np.fft.rfft2(template[::-1, ::-1], s=shape), s=shape)
    return full[th - 1:h, tw - 1:w]


def loss_surface(probability, target, valid, pi, margin):
    """Equal-pixel weighted BCE for every (dy,dx), indexed from -margin."""
    check_support(target, valid)
    p = np.asarray(probability, dtype=np.float64)
    if p.shape != target.shape or not np.isfinite(p).all() or np.any((p < 0) | (p > 1)):
        raise ValueError("finite same-grid probabilities required")
    if not 0 < pi < 1:
        raise ValueError("fixed foreground fraction must be in (0,1)")
    y = shifted_core(target, 0, 0, margin).astype(np.float64)
    p = np.clip(p, 1e-6, 1 - 1e-6)
    return (_valid_correlation(-np.log(p), y / (2 * pi)) +
            _valid_correlation(-np.log1p(-p), (1 - y) / (2 * (1 - pi)))) / y.size


def select_shift(surface, margin):
    score = np.asarray(surface)
    if score.shape != (2 * margin + 1,) * 2 or not np.isfinite(score).all():
        raise ValueError("invalid complete loss surface")
    candidates = np.argwhere(score <= score.min() + 1e-12) - margin
    dy, dx = min((tuple(map(int, v)) for v in candidates),
                 key=lambda v: (v[0] ** 2 + v[1] ** 2, v[0], v[1]))
    return {"dy": dy, "dx": dx, "at_search_boundary": max(abs(dy), abs(dx)) == margin,
            "train_loss_selected": float(score[dy + margin, dx + margin]),
            "train_loss_zero": float(score[margin, margin])}


def paired_change(zero, aligned):
    """D is reduction of I, not raw risk improvement or a causal explained fraction."""
    return {"primary": zero["primary"] - aligned["primary"],
            "delta_residual_i": aligned["primary"],
            "delta_single_risk_improvement": float(np.mean([
                zero[f"loss_{v}"] - aligned[f"loss_{v}"] for v in "abuv"])),
            **{f"delta_risk_{v}": zero[f"loss_{v}"] - aligned[f"loss_{v}"]
               for v in ("a", "b", "u", "v", "au", "av", "bv", "bu", "a_tta", "b_tta")}}
