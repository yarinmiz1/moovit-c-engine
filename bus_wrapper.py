import ctypes
import os

# ---------------------------------------------------------
# 1. C-types Configuration & Structure Definition
# ---------------------------------------------------------

NAME_LEN = 21

# Define the SortType enum equivalents based on the C header
DISTANCE = 0
DURATION = 1
FREQUENCY = 2

# Define the BusLine Structure to match exactly with the C struct
class BusLine(ctypes.Structure):
    _fields_ = [
        ("name", ctypes.c_char * NAME_LEN),
        ("distance", ctypes.c_int),
        ("duration", ctypes.c_int),
        ("frequency", ctypes.c_int)
    ]

# Load the shared library
current_dir = os.path.dirname(os.path.abspath(__file__))
# We will look for either a .dll or .so file representing the compiled C code
lib_path_dll = os.path.join(current_dir, 'sortbus.dll')
lib_path_so = os.path.join(current_dir, 'libsortbus.so')

bus_lib = None
if os.path.exists(lib_path_dll):
    bus_lib = ctypes.CDLL(lib_path_dll)
elif os.path.exists(lib_path_so):
    bus_lib = ctypes.CDLL(lib_path_so)

if bus_lib:
    # Set up the signature for: void bus_bubble_sort (BusLine *start, BusLine *end);
    bus_lib.bus_bubble_sort.argtypes = [ctypes.POINTER(BusLine), ctypes.POINTER(BusLine)]
    bus_lib.bus_bubble_sort.restype = None

    # Set up the signature for: void bus_quick_sort (BusLine *start, BusLine *end, SortType sort_type);
    bus_lib.bus_quick_sort.argtypes = [ctypes.POINTER(BusLine), ctypes.POINTER(BusLine), ctypes.c_int]
    bus_lib.bus_quick_sort.restype = None

# ---------------------------------------------------------
# 2. Python Wrapper Functions (I/O Handling)
# ---------------------------------------------------------

def _convert_to_c_array(py_bus_list):
    """Helper: Converts a Python list of dictionaries to a C-array of BusLine structs."""
    num_lines = len(py_bus_list)
    BusLineArray = BusLine * num_lines
    c_array = BusLineArray()
    
    for i, bus in enumerate(py_bus_list):
        encoded_name = bus['name'].encode('utf-8')
        if len(encoded_name) >= NAME_LEN:
            raise ValueError(f"Bus name exceeds maximum length of {NAME_LEN - 1} bytes.")
        c_array[i].name = encoded_name
        c_array[i].distance = bus['distance']
        c_array[i].duration = bus['duration']
        c_array[i].frequency = bus['frequency']
        
    return c_array, num_lines

def _convert_to_py_list(c_array, num_lines):
    """Helper: Converts a C-array of BusLine structs back to a Python list of dictionaries."""
    sorted_list = []
    for i in range(num_lines):
        sorted_list.append({
            'name': c_array[i].name.decode('utf-8'),
            'distance': c_array[i].distance,
            'duration': c_array[i].duration,
            'frequency': c_array[i].frequency
        })
    return sorted_list

def sort_bus_lines_by_name(bus_lines_list):
    """
    Sorts a list of bus dictionaries lexicographically by name.
    Uses the C bus_bubble_sort algorithm.
    """
    if not bus_lib:
        raise FileNotFoundError("Compiled shared library not found. Please compile sort_bus_lines.c")
    if not bus_lines_list:
        return []

    # 1. Prepare data (Python to C)
    c_array, num_lines = _convert_to_c_array(bus_lines_list)
    
    # 2. Call the C function (Passing pointers to the start and end of the array)
    bus_lib.bus_bubble_sort(ctypes.byref(c_array[0]), ctypes.byref(c_array[num_lines - 1]))
    
    # 3. Handle result (C to Python)
    return _convert_to_py_list(c_array, num_lines)

def sort_bus_lines_by_metric(bus_lines_list, metric):
    """
    Sorts a list of bus dictionaries by a specified metric ('distance', 'duration', or 'frequency').
    Uses the C bus_quick_sort algorithm.
    """
    if not bus_lib:
        raise FileNotFoundError("Compiled shared library not found. Please compile sort_bus_lines.c")
    if not bus_lines_list:
        return []

    # Map Python string to C Enum
    if metric == "distance":
        sort_type = DISTANCE
    elif metric == "duration":
        sort_type = DURATION
    elif metric == "frequency":
        sort_type = FREQUENCY
    else:
        raise ValueError("Invalid metric. Must be 'distance', 'duration', or 'frequency'.")

    # 1. Prepare data (Python to C)
    c_array, num_lines = _convert_to_c_array(bus_lines_list)
    
    # 2. Call the C function
    bus_lib.bus_quick_sort(ctypes.byref(c_array[0]), ctypes.byref(c_array[num_lines - 1]), sort_type)
    
    # 3. Handle result (C to Python)
    return _convert_to_py_list(c_array, num_lines)
