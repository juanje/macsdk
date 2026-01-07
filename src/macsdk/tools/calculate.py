"""Math calculation tool for MACSDK agents.

This tool provides safe mathematical expression evaluation, enabling agents
to perform accurate calculations instead of relying on LLM's unreliable
arithmetic capabilities.
"""

from __future__ import annotations

import ast
import math
from typing import cast

from langchain_core.tools import tool
from simpleeval import DEFAULT_OPERATORS, simple_eval  # type: ignore[import-untyped]


# Safe wrappers for potentially dangerous math functions
def _safe_factorial(n: int | float) -> int:
    """Factorial with input limit to prevent DoS."""
    n_int = int(n)
    if n_int < 0:
        raise ValueError("Factorial is not defined for negative numbers")
    if n_int > 100:
        raise ValueError("Factorial input too large (max: 100)")
    return math.factorial(n_int)


def _safe_pow(base: float, exponent: float) -> float | int:
    """Power function with exponent limit to prevent DoS.

    Note: Returns int if both inputs are effectively integers,
    otherwise returns float (matches Python's pow() behavior).
    """
    if abs(exponent) > 1000:
        raise ValueError("Exponent too large (max: ±1000)")
    if abs(base) > 1e10:
        raise ValueError("Base too large (max: ±1e10)")
    return cast(float | int, pow(base, exponent))


# Safe math functions to expose
SAFE_MATH_FUNCTIONS = {
    # Basic math
    "abs": abs,
    "round": round,
    "min": min,
    "max": max,
    "sum": sum,
    "pow": _safe_pow,  # Protected version
    # From math module
    "sqrt": math.sqrt,
    "sin": math.sin,
    "cos": math.cos,
    "tan": math.tan,
    "log": math.log,
    "log10": math.log10,
    "log2": math.log2,
    "exp": math.exp,
    "floor": math.floor,
    "ceil": math.ceil,
    "factorial": _safe_factorial,  # Protected version
    "gcd": math.gcd,
    "degrees": math.degrees,
    "radians": math.radians,
}

# Safe constants
SAFE_CONSTANTS = {
    "pi": math.pi,
    "e": math.e,
    "tau": math.tau,
    "inf": math.inf,
}

# Override operators to use safe power function for ** operator
# and remove bitwise shift operators to prevent DoS attacks
SAFE_OPERATORS = DEFAULT_OPERATORS.copy()
# Note: This covers BOTH pow() function calls AND ** operator syntax
SAFE_OPERATORS[ast.Pow] = _safe_pow  # Override ** operator with safe version

# Remove bitwise shift operators (potential DoS: 1 << 1000000000)
# These are rarely needed for general math and can cause memory exhaustion
if ast.LShift in SAFE_OPERATORS:
    del SAFE_OPERATORS[ast.LShift]
if ast.RShift in SAFE_OPERATORS:
    del SAFE_OPERATORS[ast.RShift]


@tool
def calculate(expression: str) -> str:
    """Safely evaluate a mathematical expression using Python syntax.

    Use this tool whenever you need to perform calculations. LLMs are not
    reliable for math, so always use this tool for any numeric computation.

    Supported operations:
    - Arithmetic: +, -, *, /, //, %, **
    - Comparisons: <, >, <=, >=, ==, !=
    - Functions: sqrt, sin, cos, tan, log, log10, log2, exp, abs, round, min,
      max, sum, pow, floor, ceil, factorial, gcd, degrees, radians
    - Constants: pi, e, tau, inf

    Note: factorial and pow have input limits for safety (see below).

    Safety limits:
    - factorial: maximum input is 100
    - pow: maximum exponent is ±1000, maximum base is ±1e10

    Args:
        expression: A Python math expression (e.g., "sqrt(16) + 2**3",
                    "sin(pi/2)", "(100 * 15) / 100")

    Returns:
        The result of the calculation as a string, or an error message if invalid.

    Examples:
        calculate("2 + 2") → "4"
        calculate("sqrt(16) * 2") → "8.0"
        calculate("sin(pi/2)") → "1.0"
        calculate("(1000 * 0.15) + 500") → "650.0"
        calculate("factorial(5)") → "120"
    """
    # Validate input
    if not expression or not expression.strip():
        return (
            "Error: Empty expression provided. Please provide a valid math expression."
        )

    expression = expression.strip()

    # Limit expression length to prevent parsing DoS
    # Limit set to 1000 to accommodate verbose scientific expressions
    if len(expression) > 1000:
        return "Error: Expression too long (maximum 1000 characters)"

    try:
        # Use simpleeval with custom functions, names, and safe operators
        result = simple_eval(
            expression,
            functions=SAFE_MATH_FUNCTIONS,
            names=SAFE_CONSTANTS,
            operators=SAFE_OPERATORS,  # Use safe power operator
        )
        return str(result)
    except ZeroDivisionError:
        return f"Error: Division by zero in expression '{expression}'"
    except NameError as e:
        return f"Error: Unknown function or variable in '{expression}' - {e}"
    except SyntaxError:
        return f"Error: Invalid syntax in expression '{expression}'"
    except Exception as e:
        return f"Error: Cannot evaluate '{expression}' - {e}"
