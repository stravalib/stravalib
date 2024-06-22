from stravalib import unithelper as uh


def test_arithmetic_comparison_support():
    assert uh.meters(2) == uh.meters(2)
    assert uh.meters(2) > uh.meters(1)
    assert uh.meters(2) + uh.meters(1) == uh.meters(3)
