# B2 PSC-style toy-model sufficiency analysis

The frozen grid contains 729 parameter cells, each with 512 simulated targets. It explicitly represents radial norm, phase direction, dual frequency, wrapping/candidate selection, modulation threshold, noise, unwrap ambiguity, direction margin, decoded angle, and two endpoint-specific NRCs.

| phase-mod region | cells |
|---|---:|
| informative | 380 |
| near-random | 317 |
| reverse | 32 |
| reverse under non-extreme settings | 10 |

Decision: **SUPPORTS_MECHANISM_SUFFICIENCY**.

The model demonstrates sufficiency, not identification: ordinary radial/noise/ambiguity settings can produce informative, near-random, and reversed `phase_mod` ordering. Directional disagreement and candidate-gap signals change with the constructed phase conflict, showing how magnitude and error semantics can decouple. No toy result is used as proof of the trained PSC network; B3 real-output interventions are mandatory.
