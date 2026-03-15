"""Tests for the FastAPI simulation API."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from qkd_playground.api.app import create_app


@pytest.fixture
def client() -> TestClient:
    app = create_app()
    return TestClient(app)


class TestHealthAndProtocols:
    def test_health(self, client: TestClient) -> None:
        resp = client.get("/health")
        assert resp.status_code == 200
        assert resp.json() == {"status": "ok"}

    def test_list_protocols(self, client: TestClient) -> None:
        resp = client.get("/protocols")
        assert resp.status_code == 200
        data = resp.json()
        names = [p["name"] for p in data]
        assert "bb84" in names


class TestSimulationWorkflow:
    def test_create_simulation(self, client: TestClient) -> None:
        resp = client.post(
            "/simulation/create",
            json={"protocol": "bb84", "num_qubits": 20},
        )
        assert resp.status_code == 200
        assert "simulation_id" in resp.json()

    def test_step_through_simulation(self, client: TestClient) -> None:
        # Create
        resp = client.post(
            "/simulation/create",
            json={"protocol": "bb84", "num_qubits": 20},
        )
        sim_id = resp.json()["simulation_id"]

        # Step through all phases
        phases = []
        for _ in range(10):
            resp = client.post(f"/simulation/{sim_id}/step")
            if resp.status_code != 200:
                break
            data = resp.json()
            phases.append(data["phase"])
            if data["is_complete"]:
                break

        assert "complete" in phases
        assert len(phases) == 5

    def test_get_state(self, client: TestClient) -> None:
        resp = client.post(
            "/simulation/create",
            json={"protocol": "bb84", "num_qubits": 10},
        )
        sim_id = resp.json()["simulation_id"]

        # Step once
        client.post(f"/simulation/{sim_id}/step")

        # Get state
        resp = client.get(f"/simulation/{sim_id}/state")
        assert resp.status_code == 200
        state = resp.json()
        assert state["simulation_id"] == sim_id
        assert state["num_qubits"] == 10
        assert len(state["steps"]) == 1

    def test_run_to_completion(self, client: TestClient) -> None:
        resp = client.post(
            "/simulation/create",
            json={"protocol": "bb84", "num_qubits": 30},
        )
        sim_id = resp.json()["simulation_id"]

        resp = client.post(f"/simulation/{sim_id}/run")
        assert resp.status_code == 200
        data = resp.json()
        assert data["raw_key_length"] == 30
        assert data["sifted_key_length"] > 0
        assert len(data["steps"]) == 5

    def test_run_with_eavesdropper(self, client: TestClient) -> None:
        resp = client.post(
            "/simulation/create",
            json={
                "protocol": "bb84",
                "num_qubits": 100,
                "eavesdropper": True,
            },
        )
        sim_id = resp.json()["simulation_id"]

        resp = client.post(f"/simulation/{sim_id}/run")
        assert resp.status_code == 200
        data = resp.json()
        # With eavesdropper, error rate should be elevated
        assert data["error_rate"] > 0

    def test_reset_simulation(self, client: TestClient) -> None:
        resp = client.post(
            "/simulation/create",
            json={"protocol": "bb84", "num_qubits": 15},
        )
        sim_id = resp.json()["simulation_id"]

        # Run to completion
        client.post(f"/simulation/{sim_id}/run")

        # Reset
        resp = client.post(f"/simulation/{sim_id}/reset")
        assert resp.status_code == 200

        # State should be fresh
        resp = client.get(f"/simulation/{sim_id}/state")
        state = resp.json()
        assert len(state["steps"]) == 0
        assert state["is_complete"] is False

    def test_step_after_complete_returns_400(self, client: TestClient) -> None:
        resp = client.post(
            "/simulation/create",
            json={"protocol": "bb84", "num_qubits": 10},
        )
        sim_id = resp.json()["simulation_id"]
        client.post(f"/simulation/{sim_id}/run")

        resp = client.post(f"/simulation/{sim_id}/step")
        assert resp.status_code == 400

    def test_nonexistent_simulation_returns_404(self, client: TestClient) -> None:
        resp = client.post("/simulation/fake-id/step")
        assert resp.status_code == 404


class TestValidation:
    def test_num_qubits_too_small(self, client: TestClient) -> None:
        resp = client.post(
            "/simulation/create",
            json={"protocol": "bb84", "num_qubits": 1},
        )
        assert resp.status_code == 422

    def test_num_qubits_too_large(self, client: TestClient) -> None:
        resp = client.post(
            "/simulation/create",
            json={"protocol": "bb84", "num_qubits": 9999},
        )
        assert resp.status_code == 422
