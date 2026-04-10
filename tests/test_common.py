import common
import pytest


def test_get_site_config_for_unknown_site_is_deterministic():
    cfg1 = common.get_site_config("mystery-site")
    cfg2 = common.get_site_config("mystery-site")

    assert cfg1 == cfg2
    assert cfg1["n"] >= 20
    assert "age_sd" in cfg1
    assert "noise_sd" in cfg1


def test_aggregate_statistics_rejects_empty_input():
    with pytest.raises(ValueError, match="no local statistics"):
        common.aggregate_statistics([])


def test_get_site_config_has_explicit_wrapper_sites():
    for site_name in ("p33", "p697", "ukb-rap"):
        cfg = common.get_site_config(site_name)
        assert cfg["seed"] == common.SITE_CONFIGS[site_name]["seed"]
        assert cfg["n"] == common.SITE_CONFIGS[site_name]["n"]


def test_make_result_summary_returns_expected_shape_and_stable_fit():
    local_stats = [
        common.compute_local_statistics("site-a"),
        common.compute_local_statistics("site-b"),
    ]

    summary = common.make_result_summary(local_stats)

    assert summary["feature_names"] == common.FEATURE_NAMES
    assert summary["site_names"] == ["site-a", "site-b"]
    assert summary["total_samples"] == 56
    assert summary["per_site_samples"] == {"site-a": 24, "site-b": 32}
    assert len(summary["estimated_beta"]) == len(common.TRUE_BETA)
    assert len(summary["standard_error"]) == len(common.TRUE_BETA)
    assert all(se > 0 for se in summary["standard_error"])

    assert summary["estimated_beta"] == pytest.approx(
        [2.45100467820349, 0.020197379212357706, -0.44814068708404464, 1.1219829916074384]
    )
    assert summary["standard_error"] == pytest.approx(
        [0.5791279163041391, 0.01016311566498775, 0.23623115631182887, 0.10075192447969285]
    )
