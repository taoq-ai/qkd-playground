"""Analytical key rate calculations for QKD protocols.

Pure calculation module — no Qiskit dependency. Implements standard
rate-distance formulas for BB84, B92, E91, and SARG04 protocols,
plus the PLOB bound (fundamental repeater-less limit).
"""

from __future__ import annotations

import math
from dataclasses import dataclass

# Standard fiber attenuation coefficient (dB/km)
FIBER_LOSS_DB_PER_KM = 0.2

# Error correction inefficiency factor
ERROR_CORRECTION_INEFFICIENCY = 1.16


def _binary_entropy(p: float) -> float:
    """Binary Shannon entropy H(p) = -p*log2(p) - (1-p)*log2(1-p)."""
    if p <= 0.0 or p >= 1.0:
        return 0.0
    return -p * math.log2(p) - (1.0 - p) * math.log2(1.0 - p)


def _channel_transmittance(
    distance_km: float,
    detector_efficiency: float,
    fiber_loss_db_km: float = FIBER_LOSS_DB_PER_KM,
) -> float:
    """Overall channel transmittance: eta = eta_det * 10^(-alpha*L/10)."""
    fiber_transmittance: float = 10.0 ** (-fiber_loss_db_km * distance_km / 10.0)
    return detector_efficiency * fiber_transmittance


@dataclass(frozen=True)
class RatePoint:
    """A single (distance, rate) data point."""

    distance_km: float
    rate: float  # bits per pulse


def calculate_bb84_rate(
    distance_km: float,
    detector_efficiency: float = 0.1,
    dark_count_rate: float = 1e-6,
    source_rate_hz: float = 1e9,  # noqa: ARG001
) -> float:
    """Calculate BB84 secure key rate (bits per pulse).

    R = (1/2) * Q_mu * [1 - H(e_mu) - f*H(e_mu)]

    where Q_mu is the overall gain, e_mu is the QBER, and f is the
    error correction inefficiency.
    """
    eta = _channel_transmittance(distance_km, detector_efficiency)
    y0 = 2.0 * dark_count_rate  # background/dark count yield

    # Overall gain: probability of a detection event
    q_mu = eta + y0 - eta * y0

    if q_mu <= 0:
        return 0.0

    # QBER: fraction of detection events that are errors
    e_mu = (y0 / 2.0) / q_mu
    if e_mu >= 0.5:
        return 0.0

    h_e = _binary_entropy(e_mu)
    f = ERROR_CORRECTION_INEFFICIENCY

    # BB84 sift factor = 1/2 (half the bases match)
    rate = 0.5 * q_mu * (1.0 - h_e - f * h_e)

    return max(rate, 0.0)


def calculate_b92_rate(
    distance_km: float,
    detector_efficiency: float = 0.1,
    dark_count_rate: float = 1e-6,
    source_rate_hz: float = 1e9,  # noqa: ARG001
) -> float:
    """Calculate B92 secure key rate (bits per pulse).

    Similar to BB84 but with ~25% sift rate and a different error model.
    """
    eta = _channel_transmittance(distance_km, detector_efficiency)
    y0 = 2.0 * dark_count_rate

    q_mu = eta + y0 - eta * y0
    if q_mu <= 0:
        return 0.0

    e_mu = (y0 / 2.0) / q_mu
    if e_mu >= 0.5:
        return 0.0

    h_e = _binary_entropy(e_mu)
    f = ERROR_CORRECTION_INEFFICIENCY

    # B92 sift factor = 1/4
    rate = 0.25 * q_mu * (1.0 - h_e - f * h_e)

    return max(rate, 0.0)


def calculate_e91_rate(
    distance_km: float,
    detector_efficiency: float = 0.1,
    dark_count_rate: float = 1e-6,
    source_rate_hz: float = 1e9,  # noqa: ARG001
) -> float:
    """Calculate E91 secure key rate (bits per pulse).

    E91 key rate is similar to BB84 (same sift rate and information-
    theoretic bounds when using matching-basis measurements).
    """
    # E91 has effectively the same rate formula as BB84
    return calculate_bb84_rate(
        distance_km, detector_efficiency, dark_count_rate, source_rate_hz
    )


def calculate_sarg04_rate(
    distance_km: float,
    detector_efficiency: float = 0.1,
    dark_count_rate: float = 1e-6,
    source_rate_hz: float = 1e9,  # noqa: ARG001
) -> float:
    """Calculate SARG04 secure key rate (bits per pulse).

    Similar to BB84 but with ~25% sift rate. Offers better PNS
    resilience at longer distances due to the modified sifting.
    """
    eta = _channel_transmittance(distance_km, detector_efficiency)
    y0 = 2.0 * dark_count_rate

    q_mu = eta + y0 - eta * y0
    if q_mu <= 0:
        return 0.0

    e_mu = (y0 / 2.0) / q_mu
    if e_mu >= 0.5:
        return 0.0

    h_e = _binary_entropy(e_mu)
    f = ERROR_CORRECTION_INEFFICIENCY

    # SARG04 sift factor = 1/4 (non-orthogonal pair announcement)
    rate = 0.25 * q_mu * (1.0 - h_e - f * h_e)

    return max(rate, 0.0)


def calculate_key_rate(
    protocol: str,
    distance_km: float,
    detector_efficiency: float = 0.1,
    dark_count_rate: float = 1e-6,
    source_rate_hz: float = 1e9,
) -> float:
    """Calculate secure key rate for any supported protocol.

    Args:
        protocol: One of "bb84", "b92", "e91", "sarg04".
        distance_km: Channel distance in kilometres.
        detector_efficiency: Single-photon detector efficiency (0 to 1).
        dark_count_rate: Dark count probability per pulse per detector.
        source_rate_hz: Source repetition rate (Hz). Reserved for future use.

    Returns:
        Secure key rate in bits per pulse. Returns 0.0 if the rate is
        negative (no secure key possible at this distance).
    """
    calculators = {
        "bb84": calculate_bb84_rate,
        "b92": calculate_b92_rate,
        "e91": calculate_e91_rate,
        "sarg04": calculate_sarg04_rate,
    }
    calc = calculators.get(protocol.lower())
    if calc is None:
        msg = f"Unknown protocol: {protocol}"
        raise ValueError(msg)
    return calc(distance_km, detector_efficiency, dark_count_rate, source_rate_hz)


def calculate_plob_bound(
    distance_km: float,
    detector_efficiency: float = 0.1,
) -> float:
    """Calculate the PLOB bound (Pirandola-Laurenza-Ottaviani-Banchi).

    The fundamental rate-distance limit for point-to-point QKD without
    quantum repeaters: R_PLOB = -log2(1 - eta).

    Args:
        distance_km: Channel distance in kilometres.
        detector_efficiency: Detector efficiency.

    Returns:
        Upper bound on key rate in bits per channel use.
    """
    eta = _channel_transmittance(distance_km, detector_efficiency)
    if eta <= 0.0 or eta >= 1.0:
        return 0.0 if eta <= 0.0 else float("inf")
    return -math.log2(1.0 - eta)


def generate_rate_vs_distance(
    protocol: str,
    max_distance_km: float = 200.0,
    steps: int = 100,
    detector_efficiency: float = 0.1,
    dark_count_rate: float = 1e-6,
    source_rate_hz: float = 1e9,
) -> list[RatePoint]:
    """Generate rate-vs-distance curve for a protocol.

    Args:
        protocol: Protocol name.
        max_distance_km: Maximum distance to compute.
        steps: Number of distance points.
        detector_efficiency: Detector efficiency.
        dark_count_rate: Dark count probability per pulse.
        source_rate_hz: Source repetition rate.

    Returns:
        List of RatePoint(distance_km, rate) ordered by distance.
    """
    points: list[RatePoint] = []
    for i in range(steps + 1):
        d = max_distance_km * i / steps
        r = calculate_key_rate(
            protocol, d, detector_efficiency, dark_count_rate, source_rate_hz
        )
        points.append(RatePoint(distance_km=d, rate=r))
    return points
