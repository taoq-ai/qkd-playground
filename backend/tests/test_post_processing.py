"""Tests for post-processing utilities: reconciliation and privacy amplification."""

from __future__ import annotations

from qkd_playground.adapters.post_processing import amplify_privacy, reconcile_keys
from qkd_playground.domain.models import BitValue


class TestReconcileKeys:
    """Tests for information reconciliation."""

    def test_identical_keys_no_corrections(self) -> None:
        """When keys are identical, no corrections should be made."""
        key = [BitValue.ZERO, BitValue.ONE, BitValue.ZERO, BitValue.ONE] * 4
        alice, bob, corrections = reconcile_keys(key, list(key))
        assert corrections == 0
        assert alice == key
        assert bob == key

    def test_single_bit_error(self) -> None:
        """A single-bit error should be corrected."""
        alice_key = [BitValue.ZERO, BitValue.ONE, BitValue.ZERO, BitValue.ONE] * 4
        bob_key = list(alice_key)
        # Flip one bit
        bob_key[2] = BitValue.ONE
        _, corrected_bob, corrections = reconcile_keys(alice_key, bob_key)
        assert corrections >= 1
        # Verify the corrected key matches Alice's
        assert corrected_bob == alice_key

    def test_multiple_errors_in_different_blocks(self) -> None:
        """Multiple errors in different blocks should each be corrected."""
        alice_key = [BitValue.ZERO] * 16
        bob_key = list(alice_key)
        # Flip one bit per block (blocks of 4 for 16 bits)
        bob_key[0] = BitValue.ONE
        bob_key[5] = BitValue.ONE
        _, corrected_bob, corrections = reconcile_keys(alice_key, bob_key)
        assert corrections >= 2
        assert corrected_bob == alice_key

    def test_empty_keys(self) -> None:
        """Empty keys should return empty with no corrections."""
        alice, bob, corrections = reconcile_keys([], [])
        assert alice == []
        assert bob == []
        assert corrections == 0

    def test_short_key(self) -> None:
        """Very short keys should still work."""
        alice_key = [BitValue.ZERO, BitValue.ONE]
        bob_key = [BitValue.ZERO, BitValue.ONE]
        _, corrected_bob, corrections = reconcile_keys(alice_key, bob_key)
        assert corrections == 0
        assert corrected_bob == alice_key


class TestAmplifyPrivacy:
    """Tests for privacy amplification."""

    def test_produces_shorter_key(self) -> None:
        """Amplified key should be shorter than input when error rate > 0."""
        key = [BitValue.ZERO, BitValue.ONE] * 20
        amplified, ratio = amplify_privacy(key, error_rate=0.05)
        assert len(amplified) < len(key)
        assert 0 < ratio < 1.0

    def test_zero_error_rate_retains_most_bits(self) -> None:
        """With 0% error rate, most bits should be retained."""
        key = [BitValue.ZERO, BitValue.ONE] * 20
        amplified, ratio = amplify_privacy(key, error_rate=0.0)
        # Should retain ~90% of bits
        assert ratio >= 0.85
        assert len(amplified) > 0

    def test_high_error_rate_produces_shorter_key(self) -> None:
        """High error rate should produce a much shorter key."""
        key = [BitValue.ZERO, BitValue.ONE] * 20
        amplified_low, ratio_low = amplify_privacy(key, error_rate=0.01)
        amplified_high, ratio_high = amplify_privacy(key, error_rate=0.10)
        assert ratio_high < ratio_low
        assert len(amplified_high) < len(amplified_low)

    def test_empty_key(self) -> None:
        """Empty key should return empty."""
        amplified, ratio = amplify_privacy([], error_rate=0.0)
        assert amplified == []
        assert ratio == 0.0

    def test_full_error_rate(self) -> None:
        """Error rate of 1.0 should return empty key."""
        key = [BitValue.ZERO, BitValue.ONE] * 10
        amplified, ratio = amplify_privacy(key, error_rate=1.0)
        assert amplified == []
        assert ratio == 0.0

    def test_output_contains_valid_bit_values(self) -> None:
        """All output bits should be valid BitValue enums."""
        key = [BitValue.ZERO, BitValue.ONE, BitValue.ZERO] * 10
        amplified, _ = amplify_privacy(key, error_rate=0.05)
        for bit in amplified:
            assert bit in (BitValue.ZERO, BitValue.ONE)
