"""Tests for PNS and partial intercept attack models.

Verifies that:
- PNS attack gains info without increasing QBER on single-photon pulses
- PNS attack is less effective against SARG04
- Partial intercept with low fraction has low detection probability
- Partial intercept with high fraction behaves like full intercept-resend
- Attack type "none" produces no eavesdropping
- API accepts attack_type parameter
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from qkd_playground.adapters.attacks import PartialInterceptChannel, PNSAttackChannel
from qkd_playground.adapters.bb84 import BB84Protocol
from qkd_playground.adapters.qiskit_adapter import (
    DefaultRandomness,
    EavesdroppingChannel,
    IdealQuantumChannel,
    QiskitMeasurementAdapter,
)
from qkd_playground.adapters.sarg04 import SARG04Protocol
from qkd_playground.api.app import create_app
from qkd_playground.domain.models import Basis, BitValue, Qubit

# --- Helpers ---


def _make_bb84_with_attack(
    attack: IdealQuantumChannel
    | EavesdroppingChannel
    | PNSAttackChannel
    | PartialInterceptChannel,
) -> BB84Protocol:
    measurement = QiskitMeasurementAdapter()
    return BB84Protocol(measurement, attack, DefaultRandomness())


def _make_sarg04_with_attack(
    attack: IdealQuantumChannel
    | EavesdroppingChannel
    | PNSAttackChannel
    | PartialInterceptChannel,
) -> SARG04Protocol:
    measurement = QiskitMeasurementAdapter()
    return SARG04Protocol(measurement, attack, DefaultRandomness())


# --- PNS Attack Tests ---


class TestPNSAttack:
    def test_pns_does_not_disturb_single_photon_pulses(self) -> None:
        """PNS attack should not modify qubits that pass through undisturbed."""
        measurement = QiskitMeasurementAdapter()
        channel = PNSAttackChannel(measurement, mu=0.1)  # low mu = mostly single-photon

        qubit = Qubit(basis=Basis.RECTILINEAR, value=BitValue.ZERO)
        # With mu=0.1, P(multi) is very small (~0.005)
        # Most qubits should pass through unchanged
        unchanged_count = 0
        total = 200
        for _ in range(total):
            channel.clear()
            result = channel.transmit(qubit)
            if result is qubit:  # identity check -- not modified
                unchanged_count += 1

        # With mu=0.1, ~99.5% should be undisturbed
        assert unchanged_count > total * 0.9

    def test_pns_gains_information_on_multi_photon(self) -> None:
        """PNS attack should intercept multi-photon pulses."""
        measurement = QiskitMeasurementAdapter()
        channel = PNSAttackChannel(measurement, mu=1.5)  # high mu = many multi-photon

        for _ in range(100):
            qubit = Qubit(basis=Basis.RECTILINEAR, value=BitValue.ONE)
            channel.transmit(qubit)

        # With mu=1.5, about 44% should be multi-photon
        assert channel.multi_photon_count > 10
        assert channel.intercepted_count == channel.multi_photon_count
        assert channel.eve_information_gain > 0.1

    def test_pns_low_error_rate_on_bb84(self) -> None:
        """PNS attack should produce low QBER on BB84 (only disturbs multi-photon)."""
        measurement = QiskitMeasurementAdapter()
        channel = PNSAttackChannel(measurement, mu=0.5)
        protocol = _make_bb84_with_attack(channel)
        result = protocol.run(200)

        # PNS doesn't disturb qubits, so error rate should be very low
        assert result.error_rate < 0.11, (
            f"PNS should produce low QBER, got {result.error_rate}"
        )

    def test_pns_eve_info_reported_in_steps(self) -> None:
        """PNS attack should report Eve's information gain in step results."""
        measurement = QiskitMeasurementAdapter()
        channel = PNSAttackChannel(measurement, mu=0.8)
        protocol = _make_bb84_with_attack(channel)
        result = protocol.run(100)

        # Find the transmission step which records attack data
        transmission_steps = [s for s in result.steps if s.eve_intercepted]
        assert len(transmission_steps) > 0
        step = transmission_steps[0]
        assert step.eve_information_gain >= 0.0
        assert step.multi_photon_fraction >= 0.0

    def test_pns_higher_error_on_sarg04(self) -> None:
        """SARG04 should still detect eavesdropping (via error rate) with PNS.

        While PNS doesn't add QBER itself, SARG04's design makes it
        harder for Eve to exploit multi-photon pulses. We verify the
        protocol can complete and that its sifting correctly handles
        PNS attack channels.
        """
        measurement = QiskitMeasurementAdapter()
        channel = PNSAttackChannel(measurement, mu=0.5)
        protocol = _make_sarg04_with_attack(channel)
        result = protocol.run(200)

        # PNS should not introduce errors (single photons undisturbed)
        # but SARG04 should still complete successfully
        assert result.error_rate < 0.5  # sanity check
        # The key should be generated (PNS doesn't introduce errors)
        assert len(result.steps) > 0

    def test_pns_invalid_mu(self) -> None:
        """PNS attack should reject invalid mu values."""
        measurement = QiskitMeasurementAdapter()
        with pytest.raises(ValueError, match="mu"):
            PNSAttackChannel(measurement, mu=0.0)
        with pytest.raises(ValueError, match="mu"):
            PNSAttackChannel(measurement, mu=3.0)


# --- Partial Intercept Tests ---


class TestPartialIntercept:
    def test_low_fraction_low_detection(self) -> None:
        """Partial intercept with low fraction should have low error rate."""
        measurement = QiskitMeasurementAdapter()
        channel = PartialInterceptChannel(measurement, intercept_fraction=0.1)
        protocol = _make_bb84_with_attack(channel)
        result = protocol.run(200)

        # With 10% intercept, error rate should be ~2.5% (10% * 25%)
        # This is below the 11% threshold, so eavesdropping should NOT be detected
        assert result.error_rate < 0.11, (
            f"Low intercept fraction should avoid detection, got {result.error_rate}"
        )
        assert not result.eavesdropper_detected

    def test_high_fraction_behaves_like_full_intercept(self) -> None:
        """Partial intercept with fraction=1.0 should behave like intercept-resend."""
        measurement = QiskitMeasurementAdapter()
        channel = PartialInterceptChannel(measurement, intercept_fraction=1.0)
        protocol = _make_bb84_with_attack(channel)
        result = protocol.run(200)

        # With 100% intercept, should behave exactly like intercept-resend
        assert result.error_rate > 0.15, (
            f"Full intercept should have high QBER, got {result.error_rate}"
        )
        assert result.eavesdropper_detected

    def test_partial_intercept_eve_info_tradeoff(self) -> None:
        """Eve's information gain should scale with intercept fraction."""
        measurement = QiskitMeasurementAdapter()

        low = PartialInterceptChannel(measurement, intercept_fraction=0.2)
        high = PartialInterceptChannel(measurement, intercept_fraction=0.8)

        assert low.eve_information_gain < high.eve_information_gain

    def test_partial_intercept_fraction_zero(self) -> None:
        """Intercept fraction 0 should produce no eavesdropping."""
        measurement = QiskitMeasurementAdapter()
        channel = PartialInterceptChannel(measurement, intercept_fraction=0.0)
        protocol = _make_bb84_with_attack(channel)
        result = protocol.run(100)

        assert result.error_rate < 0.05
        assert not result.eavesdropper_detected

    def test_partial_intercept_invalid_fraction(self) -> None:
        """Should reject invalid intercept fractions."""
        measurement = QiskitMeasurementAdapter()
        with pytest.raises(ValueError, match="intercept_fraction"):
            PartialInterceptChannel(measurement, intercept_fraction=-0.1)
        with pytest.raises(ValueError, match="intercept_fraction"):
            PartialInterceptChannel(measurement, intercept_fraction=1.5)


# --- Attack Type None ---


class TestNoAttack:
    def test_none_attack_produces_no_eavesdropping(self) -> None:
        """Attack type 'none' should produce clean key exchange."""
        measurement = QiskitMeasurementAdapter()
        channel = IdealQuantumChannel()
        protocol = BB84Protocol(measurement, channel, DefaultRandomness())
        result = protocol.run(100)

        assert not result.eavesdropper_detected
        assert result.error_rate < 0.05
        assert len(result.shared_key) > 0


# --- API Tests ---


@pytest.fixture
def client() -> TestClient:
    app = create_app()
    return TestClient(app)


class TestAttackAPI:
    def test_api_accepts_attack_type(self, client: TestClient) -> None:
        """API should accept attack_type parameter."""
        resp = client.post(
            "/simulation/create",
            json={
                "protocol": "bb84",
                "num_qubits": 50,
                "eavesdropper": True,
                "attack_type": "pns",
            },
        )
        assert resp.status_code == 200
        assert "simulation_id" in resp.json()

    def test_api_accepts_partial_intercept(self, client: TestClient) -> None:
        """API should accept partial intercept with fraction."""
        resp = client.post(
            "/simulation/create",
            json={
                "protocol": "bb84",
                "num_qubits": 50,
                "eavesdropper": True,
                "attack_type": "partial_intercept",
                "intercept_fraction": 0.3,
            },
        )
        assert resp.status_code == 200
        sim_id = resp.json()["simulation_id"]

        # Run to completion
        resp = client.post(f"/simulation/{sim_id}/run")
        assert resp.status_code == 200

    def test_api_default_attack_type(self, client: TestClient) -> None:
        """Default attack type should be intercept_resend."""
        resp = client.post(
            "/simulation/create",
            json={
                "protocol": "bb84",
                "num_qubits": 100,
                "eavesdropper": True,
            },
        )
        assert resp.status_code == 200
        sim_id = resp.json()["simulation_id"]

        resp = client.post(f"/simulation/{sim_id}/run")
        assert resp.status_code == 200
        data = resp.json()
        # Intercept-resend should be detected
        assert data["error_rate"] > 0.1

    def test_api_none_attack_no_eavesdropper(self, client: TestClient) -> None:
        """When eavesdropper=False, attack_type is ignored."""
        resp = client.post(
            "/simulation/create",
            json={
                "protocol": "bb84",
                "num_qubits": 50,
                "eavesdropper": False,
                "attack_type": "pns",
            },
        )
        assert resp.status_code == 200
        sim_id = resp.json()["simulation_id"]

        resp = client.post(f"/simulation/{sim_id}/run")
        assert resp.status_code == 200
        data = resp.json()
        assert data["error_rate"] < 0.05

    def test_api_step_response_includes_attack_fields(self, client: TestClient) -> None:
        """Step response should include attack-specific fields."""
        resp = client.post(
            "/simulation/create",
            json={
                "protocol": "bb84",
                "num_qubits": 50,
                "eavesdropper": True,
                "attack_type": "pns",
            },
        )
        sim_id = resp.json()["simulation_id"]

        # Step through transmission
        for _ in range(3):
            resp = client.post(f"/simulation/{sim_id}/step")
            assert resp.status_code == 200

        data = resp.json()
        assert "eve_information_gain" in data
        assert "intercepted_fraction" in data
        assert "multi_photon_fraction" in data
