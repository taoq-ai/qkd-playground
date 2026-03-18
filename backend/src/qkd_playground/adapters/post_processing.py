"""Post-processing utilities for QKD protocols.

Includes information reconciliation and privacy amplification.
"""

from __future__ import annotations

import hashlib
import math

from qkd_playground.domain.models import BitValue


def reconcile_keys(
    alice_key: list[BitValue],
    bob_key: list[BitValue],
) -> tuple[list[BitValue], list[BitValue], int]:
    """Simple binary error correction (Cascade-inspired).

    Divides the key into blocks, computes parities, and corrects
    single-bit errors per block. Returns corrected keys and number
    of corrections made.

    For educational purposes, we implement a simplified version:
    - Split key into blocks of adaptive size
    - Compare parity of each block
    - If parity differs, do a binary search within the block to find and fix the error
    """
    if not alice_key or not bob_key:
        return alice_key, bob_key, 0

    corrected_bob = list(bob_key)
    corrections = 0
    block_size = max(4, len(alice_key) // 8)

    for start in range(0, len(alice_key), block_size):
        end = min(start + block_size, len(alice_key))
        alice_parity = sum(1 for b in alice_key[start:end] if b == BitValue.ONE) % 2
        bob_parity = sum(1 for b in corrected_bob[start:end] if b == BitValue.ONE) % 2

        if alice_parity != bob_parity:
            # Binary search for the error within this block
            lo, hi = start, end
            while hi - lo > 1:
                mid = (lo + hi) // 2
                a_par = sum(1 for b in alice_key[lo:mid] if b == BitValue.ONE) % 2
                b_par = sum(1 for b in corrected_bob[lo:mid] if b == BitValue.ONE) % 2
                if a_par != b_par:
                    hi = mid
                else:
                    lo = mid
            # Flip the error bit
            corrected_bob[lo] = (
                BitValue.ONE if corrected_bob[lo] == BitValue.ZERO else BitValue.ZERO
            )
            corrections += 1

    return alice_key, corrected_bob, corrections


def amplify_privacy(
    key: list[BitValue],
    error_rate: float,
) -> tuple[list[BitValue], float]:
    """Privacy amplification using universal hashing.

    Reduces key length to remove Eve's potential information.
    The output length is determined by the error rate -- higher
    error rate means more bits must be sacrificed.

    Uses a simple hash-based approach for educational clarity.

    Returns (amplified_key, compression_ratio).
    """
    if not key or error_rate >= 1.0:
        return [], 0.0

    n = len(key)
    # Shannon entropy bound: secure bits ~ n * (1 - h(e))
    if error_rate <= 0:
        # No errors, but still sacrifice some bits for safety margin
        output_len = max(1, int(n * 0.9))
    else:
        # Binary entropy function
        h_e = -error_rate * _log2(error_rate) - (1 - error_rate) * _log2(1 - error_rate)
        # Secure fraction ~ 1 - 2*h(e) (accounts for error correction leakage)
        secure_fraction = max(0.1, 1.0 - 2 * h_e)
        output_len = max(1, int(n * secure_fraction))

    # Use hash-based extraction (Toeplitz-inspired but simplified)
    key_bytes = bytes([b.value for b in key])
    hash_digest = hashlib.sha256(key_bytes).digest()

    # Extract output_len bits from hash
    amplified: list[BitValue] = []
    for i in range(output_len):
        byte_idx = i // 8
        bit_idx = i % 8
        if byte_idx < len(hash_digest):
            bit = (hash_digest[byte_idx] >> bit_idx) & 1
            amplified.append(BitValue.ONE if bit == 1 else BitValue.ZERO)
        else:
            # If we need more bits than hash provides, rehash
            extra_hash = hashlib.sha256(hash_digest + i.to_bytes(4, "big")).digest()
            bit = (extra_hash[0] >> (i % 8)) & 1
            amplified.append(BitValue.ONE if bit == 1 else BitValue.ZERO)

    ratio = output_len / n if n > 0 else 0.0
    return amplified, ratio


def _log2(x: float) -> float:
    """Safe log base 2."""
    if x <= 0:
        return 0.0
    return math.log2(x)
