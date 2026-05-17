import streamlit as st
import bus_wrapper

st.set_page_config(page_title="Moovit C-Engine", layout="centered")

st.title("🚌 Moovit C-Engine: Lite Version")
st.write("If you can see this, Folium was the one crashing the app!")

dummy_buses = [
    {"name": "415_Jerusalem", "distance": 45, "duration": 60, "frequency": 15},
    {"name": "417_Express", "distance": 40, "duration": 45, "frequency": 20},
    {"name": "Local_BeitShemesh", "distance": 12, "duration": 25, "frequency": 10}
]

st.dataframe(dummy_buses, use_container_width=True)

if st.button("Sort via C-Engine (Distance)", type="primary"):
    with st.spinner("Executing native C code..."):
        sorted_buses = bus_wrapper.sort_bus_lines_by_metric(dummy_buses, "distance")
        st.success("Sorted magically fast by your C library!")
        st.dataframe(sorted_buses, use_container_width=True)