import ctypes
import os

# Get the absolute path to the shared library in the current directory
current_dir = os.path.dirname(os.path.abspath(__file__))
lib_path = os.path.join(current_dir, 'libfib.so')

# Load the shared library
fib_lib = ctypes.CDLL(lib_path)

# Explicitly define the argument types and return type for CFib
fib_lib.CFib.argtypes = [ctypes.c_int]
fib_lib.CFib.restype = ctypes.c_int

def fib(n):
    """Calls the C Fibonacci function through the shared library."""
    return fib_lib.CFib(n)
