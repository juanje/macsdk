"""Tests for calculate tool bitwise operator restrictions."""

from __future__ import annotations

from macsdk.tools.calculate import calculate


class TestCalculateBitwiseRestrictions:
    """Test suite for bitwise operator security restrictions."""

    def test_bitwise_left_shift_blocked(self) -> None:
        """Test that left shift operator is blocked to prevent DoS."""
        result = calculate.invoke({"expression": "1 << 10"})
        assert "Error" in result
        # simpleeval reports removed operators as "does not exist"
        assert "does not exist" in result.lower() or "not supported" in result.lower()

    def test_bitwise_right_shift_blocked(self) -> None:
        """Test that right shift operator is blocked."""
        result = calculate.invoke({"expression": "1024 >> 2"})
        assert "Error" in result
        # simpleeval reports removed operators as "does not exist"
        assert "does not exist" in result.lower() or "not supported" in result.lower()

    def test_regular_power_still_works(self) -> None:
        """Test that power operator (not bitshift) still works."""
        result = calculate.invoke({"expression": "2 ** 10"})
        assert "1024" in result
        assert "Error" not in result

    def test_bitwise_and_or_xor_still_allowed(self) -> None:
        """Test that non-shift bitwise operators are still available."""
        # These don't have the same DoS risk as shifts
        result_and = calculate.invoke({"expression": "5 & 3"})
        assert "1" in result_and

        result_or = calculate.invoke({"expression": "5 | 3"})
        assert "7" in result_or

        result_xor = calculate.invoke({"expression": "5 ^ 3"})
        assert "6" in result_xor
