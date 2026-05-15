import pytest
from fib_module import fib

def test_fib_zero():
    """Test the base case for n=0"""
    assert fib(0) == 0

def test_fib_one():
    """Test the base case for n=1"""
    assert fib(1) == 1

def test_fib_ten():
    """Test a larger calculation for n=10"""
    assert fib(10) == 55

def test_fib_negative():
    """Test a negative number (edge case)"""
    # Because the C code is `if (n <= 1) return n;`, passing -5 returns -5.
    assert fib(-5) == -5

def test_fib_invalid_type():
    """Test passing an invalid type like a string"""
    import ctypes
    with pytest.raises(ctypes.ArgumentError):
        fib("10")
