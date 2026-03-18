"""Tests for the analytical key rate calculation module."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from qkd_playground.adapters.key_rate import (
    calculate_b92_rate,
    calculate_bb84_rate,
    calculate_e91_rate,
    calculate_key_rate,
    calculate_plob_bound,
    calculate_sarg04_rate,
    generate_rate_vs_distance,
)
from qkd_playground.api.app import create_app


class TestKeyRateDecreases:
    """Key rate must decrease with distance."""

    @pytest.mark.parametrize("protocol", ["bb84", "b92", "e91", "sarg04"])
    def test_rate_decreases_with_distance(self, protocol: str) -> None:
        rate_short = calculate_key_rate(protocol, 10.0)
        rate_long = calculate_key_rate(protocol, 100.0)
        assert rate_short > rate_long

    @pytest.mark.parametrize("protocol", ["bb84", "b92", "e91", "sarg04"])
    def test_rate_positive_at_zero_distance(self, protocol: str) -> None:
        rate = calculate_key_rate(protocol, 0.0)
        assert rate > 0.0


class TestRateHitsZero:
    """Rate should eventually hit zero at sufficiently large distance."""

    @pytest.mark.parametrize("protocol", ["bb84", "b92", "e91", "sarg04"])
    def test_rate_reaches_zero(self, protocol: str) -> None:
        rate = calculate_key_rate(protocol, 500.0)
        assert rate == 0.0


class TestPLOBBound:
    """PLOB bound is always above individual protocol rates."""

    @pytest.mark.parametrize("protocol", ["bb84", "b92", "e91", "sarg04"])
    def test_plob_above_protocol_rate(self, protocol: str) -> None:
        for d in [10.0, 50.0, 100.0, 150.0]:
            plob = calculate_plob_bound(d)
            rate = calculate_key_rate(protocol, d)
            assert plob >= rate, (
                f"PLOB bound ({plob}) should be >= {protocol} rate ({rate}) at {d} km"
            )

    def test_plob_positive_at_short_distance(self) -> None:
        assert calculate_plob_bound(10.0) > 0.0


class TestProtocolComparisons:
    """BB84 should beat SARG04 at short distances (higher sift rate)."""

    def test_bb84_higher_than_sarg04_short_distance(self) -> None:
        bb84 = calculate_bb84_rate(10.0)
        sarg04 = calculate_sarg04_rate(10.0)
        assert bb84 > sarg04

    def test_e91_equals_bb84(self) -> None:
        """E91 rate should match BB84 (same theoretical formula)."""
        for d in [10.0, 50.0, 100.0]:
            assert calculate_e91_rate(d) == calculate_bb84_rate(d)

    def test_b92_lower_than_bb84(self) -> None:
        """B92 has a lower sift rate than BB84."""
        bb84 = calculate_bb84_rate(20.0)
        b92 = calculate_b92_rate(20.0)
        assert bb84 > b92


class TestGenerateRateVsDistance:
    def test_returns_correct_number_of_points(self) -> None:
        points = generate_rate_vs_distance("bb84", max_distance_km=100, steps=50)
        assert len(points) == 51  # 0..50 inclusive

    def test_first_point_is_zero_distance(self) -> None:
        points = generate_rate_vs_distance("bb84", steps=10)
        assert points[0].distance_km == 0.0

    def test_last_point_is_max_distance(self) -> None:
        points = generate_rate_vs_distance("bb84", max_distance_km=150, steps=10)
        assert points[-1].distance_km == pytest.approx(150.0)


class TestCalculateKeyRateDispatch:
    def test_unknown_protocol_raises(self) -> None:
        with pytest.raises(ValueError, match="Unknown protocol"):
            calculate_key_rate("unknown", 10.0)

    def test_case_insensitive(self) -> None:
        assert calculate_key_rate("BB84", 10.0) == calculate_key_rate("bb84", 10.0)


class TestPerformanceEndpoint:
    @pytest.fixture
    def client(self) -> TestClient:
        app = create_app()
        return TestClient(app)

    def test_default_params(self, client: TestClient) -> None:
        resp = client.get("/performance")
        assert resp.status_code == 200
        data = resp.json()
        assert "protocols" in data
        assert "plob_bound" in data["protocols"]
        assert "bb84" in data["protocols"]
        assert len(data["protocols"]["bb84"]) > 0

    def test_specific_protocols(self, client: TestClient) -> None:
        resp = client.get("/performance?protocols=bb84,b92")
        assert resp.status_code == 200
        data = resp.json()
        assert "bb84" in data["protocols"]
        assert "b92" in data["protocols"]
        assert "e91" not in data["protocols"]

    def test_custom_params(self, client: TestClient) -> None:
        resp = client.get(
            "/performance?protocols=bb84&max_distance=100&detector_efficiency=0.2"
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["params"]["max_distance"] == 100.0
        assert data["params"]["detector_efficiency"] == 0.2

    def test_invalid_protocols_returns_400(self, client: TestClient) -> None:
        resp = client.get("/performance?protocols=invalid")
        assert resp.status_code == 400

    def test_rate_data_has_distance_and_rate(self, client: TestClient) -> None:
        resp = client.get("/performance?protocols=bb84&steps=10")
        data = resp.json()
        point = data["protocols"]["bb84"][0]
        assert "distance" in point
        assert "rate" in point
