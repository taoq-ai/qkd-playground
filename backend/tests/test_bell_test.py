"""Tests for the CHSH Bell test simulator."""

from __future__ import annotations

import math

import pytest
from fastapi.testclient import TestClient

from qkd_playground.adapters.bell_test import BellTestSimulator
from qkd_playground.api.app import create_app


@pytest.fixture
def simulator() -> BellTestSimulator:
    return BellTestSimulator()


@pytest.fixture
def client() -> TestClient:
    app = create_app()
    return TestClient(app)


class TestBellTestSimulator:
    def test_default_chsh_violates_inequality(
        self, simulator: BellTestSimulator
    ) -> None:
        """Default CHSH angles should give S close to 2*sqrt(2) ~ 2.83."""
        result = simulator.run(num_trials=2000)
        expected = 2 * math.sqrt(2)
        assert result.s_value > 2.0, (
            f"S = {result.s_value}, expected > 2 (classical limit)"
        )
        assert abs(result.s_value - expected) < 0.5, (
            f"S = {result.s_value}, expected ~{expected:.2f}"
        )

    def test_aligned_angles_strong_correlation(
        self, simulator: BellTestSimulator
    ) -> None:
        """Both measuring at 0 deg should give E ~ +1 (perfect correlation).

        For |Phi+> with Ry rotation, E(a,b) = cos(2*(a-b)).
        At a=b=0, E = cos(0) = +1.
        """
        result = simulator.run(
            alice_angles=(0.0, 0.0),
            bob_angles=(0.0, 0.0),
            num_trials=1000,
        )
        for corr in result.correlations:
            assert corr.correlation > 0.8, (
                f"E({corr.alice_angle},{corr.bob_angle}) = {corr.correlation}, "
                f"expected ~ +1"
            )

    def test_orthogonal_angles_zero_correlation(
        self, simulator: BellTestSimulator
    ) -> None:
        """Alice at 0, Bob at 45 deg should give E ~ 0.

        E(0, 45) = cos(2*(-45)) = cos(-90) = 0.
        """
        result = simulator.run(
            alice_angles=(0.0, 0.0),
            bob_angles=(45.0, 45.0),
            num_trials=2000,
        )
        for corr in result.correlations:
            assert abs(corr.correlation) < 0.2, (
                f"E({corr.alice_angle},{corr.bob_angle}) = {corr.correlation}, "
                f"expected ~ 0"
            )

    def test_four_correlations_returned(self, simulator: BellTestSimulator) -> None:
        """Result should contain exactly four correlation entries."""
        result = simulator.run(num_trials=100)
        assert len(result.correlations) == 4

    def test_counts_sum_to_num_trials(self, simulator: BellTestSimulator) -> None:
        """Outcome counts for each angle pair should sum to num_trials."""
        num_trials = 500
        result = simulator.run(num_trials=num_trials)
        for corr in result.correlations:
            total = sum(corr.counts.values())
            assert total == num_trials

    def test_theoretical_correlation(self) -> None:
        """Verify the theoretical formula E(a,b) = cos(2*(a-b))."""
        assert BellTestSimulator.theoretical_correlation(0.0, 0.0) == pytest.approx(1.0)
        assert BellTestSimulator.theoretical_correlation(0.0, 45.0) == pytest.approx(
            0.0, abs=1e-10
        )
        assert BellTestSimulator.theoretical_correlation(0.0, 90.0) == pytest.approx(
            -1.0
        )

    def test_theoretical_s_default_angles(self) -> None:
        """Theoretical S for default angles should be 2*sqrt(2)."""
        s = BellTestSimulator.theoretical_s()
        assert s == pytest.approx(2 * math.sqrt(2), abs=1e-10)


class TestBellTestAPI:
    def test_bell_test_endpoint_default(self, client: TestClient) -> None:
        """POST /bell-test with defaults returns valid response."""
        resp = client.post("/bell-test", json={})
        assert resp.status_code == 200
        data = resp.json()
        assert "s_value" in data
        assert "correlations" in data
        assert len(data["correlations"]) == 4
        assert data["num_trials"] == 1000
        # Should violate classical bound
        assert data["s_value"] > 2.0

    def test_bell_test_endpoint_custom_angles(self, client: TestClient) -> None:
        """POST /bell-test with custom angles returns valid response."""
        resp = client.post(
            "/bell-test",
            json={
                "alice_angles": [0.0, 90.0],
                "bob_angles": [45.0, 135.0],
                "num_trials": 500,
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["num_trials"] == 500
        assert len(data["correlations"]) == 4
        for corr in data["correlations"]:
            assert "counts" in corr
            assert "correlation" in corr

    def test_bell_test_endpoint_validation(self, client: TestClient) -> None:
        """Num trials below minimum should return 422."""
        resp = client.post("/bell-test", json={"num_trials": 10})
        assert resp.status_code == 422
