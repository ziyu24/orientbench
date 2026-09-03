from orientbench.r008.audit import canonical_long, fixtures, rp1
def test_r008_geometry_contract():
 assert rp1(canonical_long(10,4,2),canonical_long(-80,2,4)) < 1e-9
 assert all(fixtures().values())
