from orientbench.r007.qualification import axial_deg, bin_index, fixture_report, rp1_distance


def test_r007_rp1_and_fixed_bins():
    assert axial_deg(180.0) == 0.0
    assert rp1_distance(10.0, 190.0) == 0.0
    assert [bin_index(x) for x in (0.0, 9.999, 10.0, 180.0)] == [0, 0, 1, 0]
    assert all(fixture_report().values())
