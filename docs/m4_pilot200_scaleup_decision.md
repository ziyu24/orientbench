# M4 200-pair pilot scale-up decision

Status: **PASS - proceed to the frozen 1,500-instance target.**

The two independent annotators covered the same 200 canonical instances. There
are 149 usable angle pairs: 38 DIOR-R, 60 FAIR1M, and 51 SODA-A. Mean
pi-periodic disagreement is 2.0938 degrees (image-cluster bootstrap 95% CI
1.8016 to 2.3932), median is 1.7137 degrees, p90 is 4.5579 degrees, and p95 is
5.5849 degrees. Eleven pairs exceed 5 degrees; none of 149 exceeds 10 degrees.

The ar>=2.1 primary subset has 100 usable pairs and mean disagreement 1.9702
degrees (95% CI 1.6360 to 2.3393). Agreement is directionally consistent across
all three datasets. Disagreement is higher for small objects and the
1.6<=ar<2.1 band, supporting the preregistered noise-sensitive treatment of the
5-degree endpoint and the ar>=2.1 primary boundary.

The pilot is adequate to validate the annotation protocol, but not adequate for
final class-, size-, and tail-stratified paper claims. The scientific return
therefore justifies continuing to the frozen 500 instances per dataset. Five A
tasks remain pending and must be resolved before the final analysis.
