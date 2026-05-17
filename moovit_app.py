import os
import subprocess
import streamlit as st

# ======================================================================
# CRITICAL CLOUD INIT: Compile the C library BEFORE importing the wrapper
# ======================================================================
SO_FILE = "libsortbus.so"
C_FILE = "sort_bus_lines.c"

# Check if we are running on a fresh Streamlit Cloud container
if not os.path.exists(SO_FILE):
    st.info("First run detected on Cloud Server. Compiling Native C Library...")
    try:
        # Run the exact GCC command to compile the shared library
        subprocess.run(
            ["gcc", "-shared", "-o", SO_FILE, "-fPIC", C_FILE],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        st.success("C Library compiled successfully!")
    except subprocess.CalledProcessError as e:
        st.error(f"Failed to compile C library. Make sure build-essential is installed.\nError: {e.stderr.decode('utf-8')}")
        st.stop()
    except FileNotFoundError:
        st.error("GCC compiler not found. Make sure 'build-essential' is in packages.txt")
        st.stop()

# Now it is completely safe to import the wrapper, as libsortbus.so is guaranteed to exist
import bus_wrapper

# ======================================================================
# STREAMLIT UI
# ======================================================================
st.set_page_config(page_title="Moovit C-Engine", layout="centered")
st.title("🚌 Moovit C-Engine: Cloud Edition")
st.markdown("Welcome to the Moovit Cloud portal. This pure Python frontend offloads all heavy-duty sorting logic to our custom hardware-accelerated C Engine.")

# Hardcoded Dummy Bus Routes (Names strictly <= 20 chars for C safety)
dummy_buses = [
    {"name": "415_Jerusalem", "distance": 45, "duration": 60, "frequency": 15},
    {"name": "417_Express", "distance": 40, "duration": 45, "frequency": 20},
    {"name": "418_Night", "distance": 48, "duration": 55, "frequency": 60},
    {"name": "Local_BeitShemesh", "distance": 12, "duration": 25, "frequency": 10},
    {"name": "420_Direct", "distance": 38, "duration": 40, "frequency": 30}
]

st.subheader("📋 Available Routes")
st.dataframe(dummy_buses, use_container_width=True)

st.divider()

st.subheader("⚡ Hardware Accelerated Sort")
sort_method = st.selectbox("Select Metric:", ["distance", "duration", "frequency", "name"])

if st.button("Sort via C-Engine", type="primary"):
    with st.spinner('Accessing Shared Object Memory...'):
        try:
            # Call the untouched C Wrapper
            if sort_method == "name":
                sorted_buses = bus_wrapper.sort_bus_lines_by_name(dummy_buses)
            else:
                sorted_buses = bus_wrapper.sort_bus_lines_by_metric(dummy_buses, sort_method)
            
            st.success(f"Successfully sorted by {sort_method} at native C speed!")
            st.dataframe(sorted_buses, use_container_width=True)
            
            # Basic Streamlit Bar Chart
            if sort_method != "name":
                st.subheader(f"📊 Visualization: {sort_method.capitalize()}")
                # Extract data for the chart
                chart_data = {bus["name"]: bus[sort_method] for bus in sorted_buses}
                st.bar_chart(chart_data)
                
        except Exception as e:
            st.error(f"Error during sorting: {e}")
