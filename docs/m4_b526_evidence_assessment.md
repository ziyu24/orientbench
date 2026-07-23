# M4 evidence assessment at 526 matched targets

The current tranche contains 526 independently annotated, same-canonical
targets and 393 usable angle pairs. The primary human-noise anchor is supported:
mean pi-periodic disagreement is 2.3587 degrees (image-cluster bootstrap 95% CI
2.0096 to 2.8696), median is 1.6435 degrees, p90 is 4.4043 degrees, and p95 is
5.8572 degrees. P(disagreement >5 degrees) is 7.63%, while
P(disagreement >10 degrees) is 1.02%.

The direction is stable relative to the 200-target pilot. DIOR-R and FAIR1M
have no >10-degree usable pair in this tranche. SODA-A contains all four
>10-degree pairs, including one 84.22-degree disagreement; this observation is
retained and must not be removed post hoc. Small objects and the
1.6<=aspect-ratio<2.1 band remain noisier. The ar>=2.1 primary subset contains
275 usable pairs and supports the existing label-noise-aware boundary.

This is sufficient for the aggregate human-annotation anchor and broad
dataset-level evidence. It is not sufficient to declare the preregistered human
work complete: target counts are 170 DIOR-R, 177 FAIR1M, and 179 SODA-A, below
the minimum of 200 per dataset. The smallest protocol-compliant next tranche is
therefore 30, 23, and 21 additional matched targets respectively (74 total).
The full 500-per-dataset target remains necessary only if the manuscript keeps
formal class-, size-, and tail-stratified claims requiring that depth.
