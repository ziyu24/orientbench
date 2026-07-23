# M4 minimum-protocol assessment at 600 targets

The minimum protocol is complete: 600 independently double-annotated targets,
exactly 200 per dataset, with no pending decisions. There are 450 primary
numeric angle pairs (122 DIOR-R, 169 FAIR1M, 159 SODA-A).

Primary pi-periodic disagreement has mean 2.3112 degrees (image-cluster
bootstrap 95% CI 1.9970 to 2.7854), median 1.6359 degrees, p90 4.4220 degrees,
and p95 5.9359 degrees. P(disagreement >5 degrees) is 8.00%, while
P(disagreement >10 degrees) is 0.89%. The ar>=2.1 subset contains 308 pairs and
retains the same direction. Results are stable across the 200-, 526-, and
600-target checkpoints.

Of 29 one-sided ambiguous/skip cases selected for blinded recheck, 27 produced
numeric angles. Their mean disagreement from the original counterpart is
2.2126 degrees and median is 1.9302 degrees; two remained ambiguous. These are
secondary results and do not overwrite the primary annotations.

This sample supports the aggregate human-noise anchor, broad dataset-level
comparisons, the 5-degree noise-sensitive qualification, and the ar>=2.1 main
boundary. Continuing to 1,500 is not necessary for those claims. It is needed
only if the manuscript retains formal rare-class, size, or extreme-tail
stratified claims.
