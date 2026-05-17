import os
import subprocess
import streamlit as st
import pandas as pd

# ======================================================================
# CRITICAL CLOUD INIT: Compile the C library BEFORE importing the wrapper
# ======================================================================
SO_FILE = "libsortbus.so"
C_FILE = "sort_bus_lines.c"

# Check if we are running on a fresh Streamlit Cloud container
if not os.path.exists(SO_FILE):
    st.info("הפעלה ראשונה בענן. מקמפל ספריות C...")
    try:
        # Run the exact GCC command to compile the shared library
        subprocess.run(
            ["gcc", "-shared", "-o", SO_FILE, "-fPIC", C_FILE],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        st.success("הספרייה קומפלה בהצלחה!")
    except subprocess.CalledProcessError as e:
        st.error(f"שגיאה בקימפול.\nError: {e.stderr.decode('utf-8')}")
        st.stop()
    except FileNotFoundError:
        st.error("לא נמצא מהדר GCC.")
        st.stop()

# Now it is completely safe to import the wrapper, as libsortbus.so is guaranteed to exist
import bus_wrapper

# ======================================================================
# STREAMLIT UI - HEBREW RTL & MODERN CSS
# ======================================================================
st.set_page_config(page_title="Moovit מנוע C", layout="centered")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Heebo:wght@400;700&display=swap');

/* Main RTL and Font */
.stApp {
    font-family: 'Heebo', sans-serif !important;
    direction: rtl !important;
    text-align: right !important;
    background-color: #f7f9fa;
}

/* Override all markdown and headers to be RTL */
.stMarkdown, p, h1, h2, h3, h4, h5, h6, .stSelectbox label {
    direction: rtl !important;
    text-align: right !important;
}

/* Modern Button Styling (Moovit Orange) */
.stButton>button {
    background-color: #ff6a00 !important;
    color: white !important;
    border-radius: 20px !important;
    border: none !important;
    padding: 10px 24px !important;
    font-weight: 700 !important;
    font-size: 16px !important;
    transition: all 0.3s ease !important;
    width: 100%;
}

.stButton>button:hover {
    background-color: #e65c00 !important;
    transform: translateY(-2px);
    box-shadow: 0 4px 12px rgba(255, 106, 0, 0.3);
}

/* DataFrame container styling */
[data-testid="stDataFrame"] {
    direction: rtl !important;
    background-color: white;
    border-radius: 12px;
    padding: 10px;
    box-shadow: 0 2px 8px rgba(0,0,0,0.05);
}
</style>
""", unsafe_allow_html=True)

st.title("🚌 Moovit: מנוע C מתקדם")
st.markdown("ממשק זה מריץ פייתון, אך כל הלוגיקה הכבדה של מיון הקווים מתבצעת ברקע על ידי מנוע C טבעי ומהיר!")

# Hardcoded Dummy Bus Routes
# CRITICAL: UTF-8 Encoded lengths must be strictly <= 20 bytes for the C buffer!
# '415_ירושלים' = 18 bytes
# '417_אקספרס' = 16 bytes
# '418_לילה' = 12 bytes
# '10_פנימי' = 13 bytes
# '420_ישיר' = 12 bytes
dummy_buses = [
    {"name": "415_ירושלים", "distance": 45, "duration": 60, "frequency": 15},
    {"name": "417_אקספרס", "distance": 40, "duration": 45, "frequency": 20},
    {"name": "418_לילה", "distance": 48, "duration": 55, "frequency": 60},
    {"name": "10_פנימי", "distance": 12, "duration": 25, "frequency": 10},
    {"name": "420_ישיר", "distance": 38, "duration": 40, "frequency": 30}
]

def format_buses_for_display(buses_list):
    """Formats the Python dictionary list into a readable Hebrew Pandas DataFrame"""
    df = pd.DataFrame(buses_list)
    df = df.rename(columns={
        "name": "שם הקו",
        "distance": "מרחק (ק״מ)",
        "duration": "זמן נסיעה (דקות)",
        "frequency": "תדירות (דקות)"
    })
    return df

st.subheader("📋 קווים זמינים (לפני מיון)")
st.dataframe(format_buses_for_display(dummy_buses), use_container_width=True)

st.divider()

st.subheader("⚡ מיון מואץ-חומרה")

# Map Hebrew dropdown options to the English keys expected by the C Wrapper
sort_options = {
    "מרחק": "distance",
    "זמן נסיעה": "duration",
    "תדירות": "frequency",
    "שם הקו": "name"
}

selected_label = st.selectbox("בחר מדד למיון הקווים:", list(sort_options.keys()))
sort_method = sort_options[selected_label]

if st.button("מיין באמצעות מנוע C", type="primary"):
    with st.spinner('ניגש לזיכרון ה-Shared Object...'):
        try:
            # Call the untouched C Wrapper with the English keys it expects
            if sort_method == "name":
                sorted_buses = bus_wrapper.sort_bus_lines_by_name(dummy_buses)
            else:
                sorted_buses = bus_wrapper.sort_bus_lines_by_metric(dummy_buses, sort_method)
            
            st.success(f"המיון עבר בהצלחה לפי {selected_label} במהירות שיא!")
            st.dataframe(format_buses_for_display(sorted_buses), use_container_width=True)
            
            # Basic Streamlit Bar Chart
            if sort_method != "name":
                st.subheader(f"📊 תצוגה גרפית: {selected_label}")
                chart_data = {bus["name"]: bus[sort_method] for bus in sorted_buses}
                st.bar_chart(chart_data)
                
        except Exception as e:
            st.error(f"שגיאה במהלך המיון: {e}")
