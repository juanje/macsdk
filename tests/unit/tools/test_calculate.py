"""Unit tests for calculate tool."""

from __future__ import annotations

import pytest

from macsdk.tools.calculate import calculate


class TestCalculateTool:
    """Test suite for the calculate tool."""

    def test_basic_arithmetic(self) -> None:
        """Test basic arithmetic operations."""
        assert calculate.invoke({"expression": "2 + 2"}) == "4"
        assert calculate.invoke({"expression": "10 - 5"}) == "5"
        assert calculate.invoke({"expression": "3 * 4"}) == "12"
        assert calculate.invoke({"expression": "15 / 3"}) == "5.0"

    def test_order_of_operations(self) -> None:
        """Test that order of operations is respected."""
        assert calculate.invoke({"expression": "2 + 3 * 4"}) == "14"
        assert calculate.invoke({"expression": "(2 + 3) * 4"}) == "20"

    def test_exponentiation(self) -> None:
        """Test power operations."""
        assert calculate.invoke({"expression": "2 ** 3"}) == "8"
        assert calculate.invoke({"expression": "pow(2, 3)"}) == "8"

    def test_math_functions(self) -> None:
        """Test mathematical functions."""
        assert calculate.invoke({"expression": "sqrt(16)"}) == "4.0"
        assert calculate.invoke({"expression": "abs(-5)"}) == "5"
        assert calculate.invoke({"expression": "round(3.7)"}) == "4"
        assert calculate.invoke({"expression": "floor(3.7)"}) == "3"
        assert calculate.invoke({"expression": "ceil(3.2)"}) == "4"

    def test_trigonometric_functions(self) -> None:
        """Test trigonometric functions."""
        # sin(pi/2) should be 1.0
        result = calculate.invoke({"expression": "sin(pi/2)"})
        assert float(result) == pytest.approx(1.0)

        # cos(0) should be 1.0
        result = calculate.invoke({"expression": "cos(0)"})
        assert float(result) == pytest.approx(1.0)

    def test_logarithmic_functions(self) -> None:
        """Test logarithmic functions."""
        assert calculate.invoke({"expression": "log10(100)"}) == "2.0"
        assert calculate.invoke({"expression": "log2(8)"}) == "3.0"

        # log(e) should be 1.0
        result = calculate.invoke({"expression": "log(e)"})
        assert float(result) == pytest.approx(1.0)

    def test_constants(self) -> None:
        """Test mathematical constants."""
        # pi is approximately 3.14159
        result = calculate.invoke({"expression": "pi"})
        assert float(result) == pytest.approx(3.14159, rel=1e-4)

        # e is approximately 2.71828
        result = calculate.invoke({"expression": "e"})
        assert float(result) == pytest.approx(2.71828, rel=1e-4)

        # tau is approximately 6.28318
        result = calculate.invoke({"expression": "tau"})
        assert float(result) == pytest.approx(6.28318, rel=1e-4)

    def test_complex_expression(self) -> None:
        """Test a complex expression."""
        result = calculate.invoke({"expression": "sqrt(16) + 2**3 + log10(100)"})
        assert float(result) == pytest.approx(14.0)

    def test_factorial(self) -> None:
        """Test factorial function."""
        assert calculate.invoke({"expression": "factorial(5)"}) == "120"
        assert calculate.invoke({"expression": "factorial(0)"}) == "1"

    def test_min_max_sum(self) -> None:
        """Test min, max, and sum functions."""
        assert calculate.invoke({"expression": "min(5, 2, 8)"}) == "2"
        assert calculate.invoke({"expression": "max(5, 2, 8)"}) == "8"
        # sum needs tuple/list syntax which simpleeval supports differently
        assert calculate.invoke({"expression": "1 + 2 + 3 + 4"}) == "10"

    def test_division_by_zero(self) -> None:
        """Test that division by zero returns an error message."""
        result = calculate.invoke({"expression": "10 / 0"})
        assert "Error" in result
        assert "division by zero" in result.lower()

    def test_invalid_syntax(self) -> None:
        """Test that invalid syntax returns an error message."""
        result = calculate.invoke({"expression": "2 +* 3"})
        assert "Error" in result

    def test_unknown_function(self) -> None:
        """Test that unknown functions return an error message."""
        result = calculate.invoke({"expression": "unknown_func(5)"})
        assert "Error" in result

    def test_empty_expression(self) -> None:
        """Test that empty expression returns an error message."""
        result = calculate.invoke({"expression": ""})
        assert "Error" in result
        assert "empty" in result.lower()

    def test_whitespace_handling(self) -> None:
        """Test that whitespace is handled correctly."""
        assert calculate.invoke({"expression": "  2 + 2  "}) == "4"
        assert calculate.invoke({"expression": "\n2 + 2\n"}) == "4"

    def test_percentage_calculation(self) -> None:
        """Test percentage calculations."""
        # 15% of 100
        assert calculate.invoke({"expression": "(100 * 15) / 100"}) == "15.0"
        # 20% increase
        assert calculate.invoke({"expression": "100 + (100 * 0.20)"}) == "120.0"

    def test_comparisons(self) -> None:
        """Test comparison operations."""
        assert calculate.invoke({"expression": "5 > 3"}) == "True"
        assert calculate.invoke({"expression": "5 < 3"}) == "False"
        assert calculate.invoke({"expression": "5 == 5"}) == "True"
        assert calculate.invoke({"expression": "5 != 3"}) == "True"

    def test_degrees_radians_conversion(self) -> None:
        """Test angle conversion functions."""
        # 180 degrees = pi radians
        result = calculate.invoke({"expression": "radians(180)"})
        assert float(result) == pytest.approx(3.14159, rel=1e-4)

        # pi radians = 180 degrees
        result = calculate.invoke({"expression": "degrees(pi)"})
        assert float(result) == pytest.approx(180.0)

    def test_gcd(self) -> None:
        """Test greatest common divisor."""
        assert calculate.invoke({"expression": "gcd(12, 8)"}) == "4"
        assert calculate.invoke({"expression": "gcd(17, 19)"}) == "1"

    def test_factorial_limit(self) -> None:
        """Test that factorial has a safety limit."""
        # Should work for reasonable values
        assert calculate.invoke({"expression": "factorial(10)"}) == "3628800"

        # Should reject values over 100
        result = calculate.invoke({"expression": "factorial(101)"})
        assert "Error" in result
        assert "too large" in result.lower()

    def test_pow_limits(self) -> None:
        """Test that pow has safety limits."""
        # Should work for reasonable values
        result = calculate.invoke({"expression": "pow(2, 10)"})
        assert float(result) == 1024.0

        # Should reject exponents over 1000
        result = calculate.invoke({"expression": "pow(2, 1001)"})
        assert "Error" in result
        assert "too large" in result.lower()

        # Should reject very large bases
        result = calculate.invoke({"expression": "pow(1e11, 2)"})
        assert "Error" in result
        assert "too large" in result.lower()

    def test_power_operator_uses_safe_version(self) -> None:
        """Test that ** operator also uses the safe power function."""
        # Should work for reasonable values
        result = calculate.invoke({"expression": "2 ** 10"})
        assert float(result) == 1024.0

        # Should reject large exponents via ** operator
        result = calculate.invoke({"expression": "2 ** 1001"})
        assert "Error" in result
        assert "too large" in result.lower()

    def test_expression_length_limit(self) -> None:
        """Test that very long expressions are rejected."""
        # Create an expression longer than 1000 characters
        long_expr = "1 + " * 300 + "1"  # Much longer than 1000 chars

        result = calculate.invoke({"expression": long_expr})
        assert "Error" in result
        assert "too long" in result.lower()
