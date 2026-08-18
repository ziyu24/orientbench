# SAUR-OBB Stage A method specification

SAUR augments the PSC `AngleBranchRetinaHead` rather than rescoring completed
predictions.  For every anchor, the new in-head branch predicts a residual
mean vector `(sin(2δ), cos(2δ))` and a positive concentration `κ` from the
regression feature map.  The corrected axial angle is

`θ_SAUR = wrap_axial(θ_PSC + g(w,h) * 0.5 * atan2(sin(2δ), cos(2δ)))`.

`g(w,h) = sigmoid(4 * (|log(w/h)| - .25))` is a continuous symmetry gate.  It
is invariant to swapping width and height and reduces both correction and
concentration for square-like boxes.  The branch uses the axial von-Mises
negative log likelihood

`log I0(κ) - κ cos(2 * wrap_axial(θ_GT - θ_SAUR))`,

with `κ = softplus(raw κ) * g + 1e-4` and a fixed loss weight `.25`.  Ground
truth occurs only in this training loss.  At inference the branch uses detector
features and decoded predicted boxes, returns corrected OBB angles, and emits
`saur_concentration` as its native reliability signal.  It does not use
classification score as a feature, a selector, or a post-hoc table fit.

Stage A fixed protocol: DIOR-R is user-authorized `trainval -> test`; SODA-A is
`train -> val`.  Both CONT and SAUR use the same seed, PSC start checkpoint,
three epochs, launcher, batch construction and four-GPU resource allocation.
