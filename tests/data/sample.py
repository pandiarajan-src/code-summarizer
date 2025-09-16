"""Sample Python file for testing purposes."""

import os
import sys
from typing import List, Optional


def greet(name: str, greeting: str = "Hello") -> str:
    """Greet a person with a custom message.

    Args:
        name: The name of the person to greet
        greeting: The greeting message (default: "Hello")

    Returns:
        A formatted greeting string
    """
    return f"{greeting}, {name}!"


class Calculator:
    """A simple calculator class for basic arithmetic operations."""

    def __init__(self):
        """Initialize the calculator."""
        self.history: List[str] = []

    def add(self, a: float, b: float) -> float:
        """Add two numbers.

        Args:
            a: First number
            b: Second number

        Returns:
            The sum of a and b
        """
        result = a + b
        self.history.append(f"{a} + {b} = {result}")
        return result

    def subtract(self, a: float, b: float) -> float:
        """Subtract two numbers.

        Args:
            a: First number
            b: Second number

        Returns:
            The difference of a and b
        """
        result = a - b
        self.history.append(f"{a} - {b} = {result}")
        return result

    def get_history(self) -> List[str]:
        """Get the calculation history.

        Returns:
            List of calculation strings
        """
        return self.history.copy()


def main() -> Optional[int]:
    """Main function to demonstrate the calculator."""
    calc = Calculator()

    print(greet("World"))
    print(greet("Python", "Hi"))

    # Perform some calculations
    result1 = calc.add(10, 5)
    result2 = calc.subtract(20, 8)

    print(f"10 + 5 = {result1}")
    print(f"20 - 8 = {result2}")

    # Show history
    print("\nCalculation history:")
    for entry in calc.get_history():
        print(f"  {entry}")

    return 0


if __name__ == "__main__":
    sys.exit(main() or 0)