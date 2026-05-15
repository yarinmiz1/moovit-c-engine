import pytest
from bus_wrapper import sort_bus_lines_by_name, sort_bus_lines_by_metric

# ---------------------------------------------------------
# Test Fixtures (Sample Data)
# ---------------------------------------------------------

@pytest.fixture
def sample_buses():
    """Returns a fresh, unsorted list of bus dictionaries for each test."""
    return [
        {'name': '55a', 'distance': 150, 'duration': 45, 'frequency': 15},
        {'name': '10',  'distance': 100, 'duration': 30, 'frequency': 10},
        {'name': '99',  'distance': 250, 'duration': 90, 'frequency': 30},
        {'name': '10',  'distance': 50,  'duration': 20, 'frequency': 5} # duplicate name edge case
    ]

# ---------------------------------------------------------
# Valid Sorting Tests
# ---------------------------------------------------------

def test_sort_by_name(sample_buses):
    """Test bubble sort lexicographically by name."""
    sorted_buses = sort_bus_lines_by_name(sample_buses)
    
    # Expected order: '10', '10', '55a', '99'
    assert sorted_buses[0]['name'] == '10'
    assert sorted_buses[1]['name'] == '10'
    assert sorted_buses[2]['name'] == '55a'
    assert sorted_buses[3]['name'] == '99'

def test_sort_by_distance(sample_buses):
    """Test quick sort by distance."""
    sorted_buses = sort_bus_lines_by_metric(sample_buses, 'distance')
    
    # Expected order: 50, 100, 150, 250
    assert sorted_buses[0]['distance'] == 50
    assert sorted_buses[1]['distance'] == 100
    assert sorted_buses[2]['distance'] == 150
    assert sorted_buses[3]['distance'] == 250

def test_sort_by_duration(sample_buses):
    """Test quick sort by duration."""
    sorted_buses = sort_bus_lines_by_metric(sample_buses, 'duration')
    
    # Expected order: 20, 30, 45, 90
    assert sorted_buses[0]['duration'] == 20
    assert sorted_buses[1]['duration'] == 30
    assert sorted_buses[2]['duration'] == 45
    assert sorted_buses[3]['duration'] == 90

def test_sort_by_frequency(sample_buses):
    """Test quick sort by frequency."""
    sorted_buses = sort_bus_lines_by_metric(sample_buses, 'frequency')
    
    # Expected order: 5, 10, 15, 30
    assert sorted_buses[0]['frequency'] == 5
    assert sorted_buses[1]['frequency'] == 10
    assert sorted_buses[2]['frequency'] == 15
    assert sorted_buses[3]['frequency'] == 30

# ---------------------------------------------------------
# Invalid Input Handling
# ---------------------------------------------------------

def test_empty_list():
    """Test that passing an empty list returns an empty list without crashing C."""
    assert sort_bus_lines_by_name([]) == []
    assert sort_bus_lines_by_metric([], 'distance') == []

def test_invalid_metric(sample_buses):
    """Test that passing an invalid metric string raises a ValueError."""
    with pytest.raises(ValueError, match="Invalid metric"):
        sort_bus_lines_by_metric(sample_buses, 'speed')

def test_name_too_long():
    """Test that passing a name that is too long raises a ValueError."""
    long_name_bus = [{'name': 'a' * 21, 'distance': 10, 'duration': 10, 'frequency': 10}]
    with pytest.raises(ValueError, match="Bus name exceeds maximum length"):
        sort_bus_lines_by_name(long_name_bus)

# ---------------------------------------------------------
# Edge Cases
# ---------------------------------------------------------

def test_single_element_list():
    """Test sorting a list with only one element."""
    single_bus = [{'name': '1', 'distance': 10, 'duration': 10, 'frequency': 10}]
    
    # Should not crash and should return the identical list
    assert sort_bus_lines_by_name(single_bus) == single_bus
    assert sort_bus_lines_by_metric(single_bus, 'distance') == single_bus

def test_already_sorted_list():
    """Test sorting a list that is already sorted."""
    sorted_buses = [
        {'name': 'a', 'distance': 10, 'duration': 10, 'frequency': 10},
        {'name': 'b', 'distance': 20, 'duration': 20, 'frequency': 20},
        {'name': 'c', 'distance': 30, 'duration': 30, 'frequency': 30}
    ]
    
    result = sort_bus_lines_by_metric(sorted_buses, 'distance')
    assert result == sorted_buses

def test_reverse_sorted_list():
    """Test sorting a list that is in exactly reverse order."""
    reverse_buses = [
        {'name': 'c', 'distance': 30, 'duration': 30, 'frequency': 30},
        {'name': 'b', 'distance': 20, 'duration': 20, 'frequency': 20},
        {'name': 'a', 'distance': 10, 'duration': 10, 'frequency': 10}
    ]
    
    result = sort_bus_lines_by_metric(reverse_buses, 'distance')
    assert result[0]['distance'] == 10
    assert result[1]['distance'] == 20
    assert result[2]['distance'] == 30
