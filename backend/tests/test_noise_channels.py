"""Tests for quantum channel noise models."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from qkd_playground.adapters.qiskit_adapter import (
    CompositeChannel,
    EavesdroppingChannel,
    IdealQuantumChannel,
    NoisyChannel,
    QiskitMeasurementAdapter,
)
from qkd_playground.api.app import create_app
from qkd_playground.domain.models import Basis, BitValue, Qubit


class TestNoisyChannel:
    def test_zero_noise_passes_through(self) -> None:
        """With zero noise and zero loss, qubit passes through unchanged."""
        channel = NoisyChannel(depolarizing_rate=0.0, loss_rate=0.0)
        qubit = Qubit(basis=Basis.RECTILINEAR, value=BitValue.ONE)
        for _ in range(100):
            result = channel.transmit(qubit)
            assert result == qubit

    def test_full_depolarization_randomizes(self) -> None:
        """With 100% depolarization, output should be random (not always same)."""
        channel = NoisyChannel(depolarizing_rate=1.0, loss_rate=0.0)
        qubit = Qubit(basis=Basis.RECTILINEAR, value=BitValue.ZERO)
        results = {channel.transmit(qubit) for _ in range(200)}
        # With 100% depolarization over 200 trials, we should see
        # at least 2 different outputs (all 4 possible qubits likely)
        assert len(results) > 1

    def test_full_loss_randomizes(self) -> None:
        """With 100% loss, output should be random."""
        channel = NoisyChannel(depolarizing_rate=0.0, loss_rate=1.0)
        qubit = Qubit(basis=Basis.RECTILINEAR, value=BitValue.ZERO)
        results = {channel.transmit(qubit) for _ in range(200)}
        assert len(results) > 1

    def test_moderate_noise_introduces_some_errors(self) -> None:
        """With moderate noise, some qubits should be altered."""
        channel = NoisyChannel(depolarizing_rate=0.3, loss_rate=0.0)
        qubit = Qubit(basis=Basis.RECTILINEAR, value=BitValue.ONE)
        changed = sum(1 for _ in range(500) if channel.transmit(qubit) != qubit)
        # Expect roughly 30% changed, allow wide margin
        assert changed > 50  # at least 10% changed
        assert changed < 400  # not all changed

    def test_invalid_depolarizing_rate(self) -> None:
        with pytest.raises(ValueError, match="depolarizing_rate"):
            NoisyChannel(depolarizing_rate=-0.1)
        with pytest.raises(ValueError, match="depolarizing_rate"):
            NoisyChannel(depolarizing_rate=1.5)

    def test_invalid_loss_rate(self) -> None:
        with pytest.raises(ValueError, match="loss_rate"):
            NoisyChannel(loss_rate=-0.1)
        with pytest.raises(ValueError, match="loss_rate"):
            NoisyChannel(loss_rate=1.5)


class TestCompositeChannel:
    def test_empty_composite_passes_through(self) -> None:
        """Composite with no channels passes through unchanged."""
        channel = CompositeChannel([])
        qubit = Qubit(basis=Basis.DIAGONAL, value=BitValue.ONE)
        assert channel.transmit(qubit) == qubit

    def test_single_channel_composite(self) -> None:
        """Composite with single ideal channel passes through."""
        channel = CompositeChannel([IdealQuantumChannel()])
        qubit = Qubit(basis=Basis.RECTILINEAR, value=BitValue.ZERO)
        assert channel.transmit(qubit) == qubit

    def test_noise_then_eavesdropping(self) -> None:
        """Composite with noise + eavesdropping applies both effects."""
        measurement = QiskitMeasurementAdapter()
        eve_channel = EavesdroppingChannel(measurement)
        noisy = NoisyChannel(depolarizing_rate=0.5, loss_rate=0.0)
        composite = CompositeChannel([noisy, eve_channel])

        qubit = Qubit(basis=Basis.RECTILINEAR, value=BitValue.ZERO)
        # Just verify it runs without error and Eve records data
        for _ in range(10):
            composite.transmit(qubit)
        assert len(eve_channel.eve_bases) == 10
        assert len(eve_channel.eve_results) == 10

    def test_composing_two_noisy_channels(self) -> None:
        """Two noisy channels composed should introduce more noise."""
        single = NoisyChannel(depolarizing_rate=0.2, loss_rate=0.0)
        double = CompositeChannel(
            [
                NoisyChannel(depolarizing_rate=0.2, loss_rate=0.0),
                NoisyChannel(depolarizing_rate=0.2, loss_rate=0.0),
            ]
        )
        qubit = Qubit(basis=Basis.RECTILINEAR, value=BitValue.ONE)
        n_trials = 500
        single_changed = sum(
            1 for _ in range(n_trials) if single.transmit(qubit) != qubit
        )
        double_changed = sum(
            1 for _ in range(n_trials) if double.transmit(qubit) != qubit
        )
        # Double composition should generally produce more errors
        # (probabilistically, not guaranteed per-run, so use wide margins)
        assert double_changed > single_changed * 0.5  # at least not dramatically less


class TestAPINoiseParameters:
    @pytest.fixture
    def client(self) -> TestClient:
        app = create_app()
        return TestClient(app)

    def test_create_with_noise(self, client: TestClient) -> None:
        resp = client.post(
            "/simulation/create",
            json={
                "protocol": "bb84",
                "num_qubits": 20,
                "noise_level": 0.1,
                "loss_rate": 0.05,
            },
        )
        assert resp.status_code == 200
        assert "simulation_id" in resp.json()

    def test_state_includes_noise_params(self, client: TestClient) -> None:
        resp = client.post(
            "/simulation/create",
            json={
                "protocol": "bb84",
                "num_qubits": 20,
                "noise_level": 0.15,
                "loss_rate": 0.1,
            },
        )
        sim_id = resp.json()["simulation_id"]
        resp = client.get(f"/simulation/{sim_id}/state")
        state = resp.json()
        assert state["noise_level"] == 0.15
        assert state["loss_rate"] == 0.1

    def test_noise_defaults_to_zero(self, client: TestClient) -> None:
        resp = client.post(
            "/simulation/create",
            json={"protocol": "bb84", "num_qubits": 20},
        )
        sim_id = resp.json()["simulation_id"]
        resp = client.get(f"/simulation/{sim_id}/state")
        state = resp.json()
        assert state["noise_level"] == 0.0
        assert state["loss_rate"] == 0.0

    def test_run_with_noise_produces_errors(self, client: TestClient) -> None:
        """High noise should produce a non-zero error rate."""
        resp = client.post(
            "/simulation/create",
            json={
                "protocol": "bb84",
                "num_qubits": 100,
                "noise_level": 0.5,
                "loss_rate": 0.0,
            },
        )
        sim_id = resp.json()["simulation_id"]
        resp = client.post(f"/simulation/{sim_id}/run")
        assert resp.status_code == 200
        data = resp.json()
        # With 50% noise on 100 qubits, error rate should be elevated
        assert data["error_rate"] > 0

    def test_invalid_noise_level(self, client: TestClient) -> None:
        resp = client.post(
            "/simulation/create",
            json={"protocol": "bb84", "num_qubits": 20, "noise_level": 1.5},
        )
        assert resp.status_code == 422

    def test_invalid_loss_rate(self, client: TestClient) -> None:
        resp = client.post(
            "/simulation/create",
            json={"protocol": "bb84", "num_qubits": 20, "loss_rate": -0.1},
        )
        assert resp.status_code == 422
