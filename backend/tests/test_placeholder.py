"""Placeholder tests to validate CI pipeline."""

import pytest

from qkd_playground.domain.models import Basis, BitValue, Qubit


def test_qubit_creation() -> None:
    qubit = Qubit(basis=Basis.RECTILINEAR, value=BitValue.ZERO)
    assert qubit.basis == Basis.RECTILINEAR
    assert qubit.value == BitValue.ZERO


def test_qubit_is_frozen() -> None:
    qubit = Qubit(basis=Basis.DIAGONAL, value=BitValue.ONE)
    with pytest.raises(AttributeError):
        qubit.basis = Basis.RECTILINEAR  # type: ignore[misc]
