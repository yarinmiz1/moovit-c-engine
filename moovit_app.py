import os
import subprocess
import random
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
# SESSION STATE INIT (GAMES & REWARDS)
# ======================================================================
def init_game():
    BUS_PAIRS = [
        "415 בית שמש - י-ם",
        "615 תל אביב - נתניה",
        "1 חיפה - קריות",
        "480 תל אביב - י-ם",
        "390 תל אביב - אילת",
        "18 ירושלים"
    ]
    cards = BUS_PAIRS * 2
    random.shuffle(cards)
    st.session_state.board = cards
    st.session_state.flipped = [False] * 12
    st.session_state.matched = [False] * 12
    st.session_state.first_flip = None
    st.session_state.second_flip = None
    st.session_state.game_won_awarded = False

if 'moovit_coins' not in st.session_state:
    st.session_state.moovit_coins = 0
if 'games_played_today' not in st.session_state:
    st.session_state.games_played_today = 0
if 'board' not in st.session_state:
    init_game()

def flip_card(i):
    if st.session_state.matched[i] or st.session_state.flipped[i]:
        return

    # If two cards are already flipped but not matched, reset them on next click
    if st.session_state.first_flip is not None and st.session_state.second_flip is not None:
        st.session_state.flipped[st.session_state.first_flip] = False
        st.session_state.flipped[st.session_state.second_flip] = False
        st.session_state.first_flip = None
        st.session_state.second_flip = None

    if st.session_state.first_flip is None:
        st.session_state.first_flip = i
        st.session_state.flipped[i] = True
    elif st.session_state.second_flip is None:
        st.session_state.second_flip = i
        st.session_state.flipped[i] = True
        
        # Check match
        if st.session_state.board[st.session_state.first_flip] == st.session_state.board[st.session_state.second_flip]:
            st.session_state.matched[st.session_state.first_flip] = True
            st.session_state.matched[st.session_state.second_flip] = True
            st.session_state.first_flip = None
            st.session_state.second_flip = None


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

/* Disabled buttons for Memory Game (Flipped/Matched cards) */
.stButton>button:disabled {
    background-color: #f0f2f6 !important;
    color: #31333F !important;
    opacity: 1 !important;
    transform: none !important;
    box-shadow: none !important;
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

# ======================================================================
# TABS NAVIGATION
# ======================================================================
tab1, tab2 = st.tabs(["🚏 חיפוש מסלולים (C-Engine)", "🎮 משחקים ונקודות"])

# ----------------------------------------------------------------------
# TAB 1: C-ENGINE ROUTE SORTING
# ----------------------------------------------------------------------
with tab1:
    st.markdown("ממשק זה מריץ פייתון, אך כל הלוגיקה הכבדה של מיון הקווים מתבצעת ברקע על ידי מנוע C טבעי ומהיר!")

    # Realistic Nationwide Database
    nationwide_buses = [
        {"name": "480_ת\"א_י-ם", "distance": 65, "duration": 60, "frequency": 120},
        {"name": "405_ת\"א_י-ם", "distance": 63, "duration": 55, "frequency": 110},
        {"name": "415_בי\"ש_י-ם", "distance": 35, "duration": 45, "frequency": 50},
        {"name": "947_חיפה_י-ם", "distance": 150, "duration": 180, "frequency": 30},
        {"name": "910_חיפה_ת\"א", "distance": 95, "duration": 90, "frequency": 40},
        {"name": "390_ת\"א_אילת", "distance": 350, "duration": 270, "frequency": 15},
        {"name": "444_י-ם_אילת", "distance": 320, "duration": 260, "frequency": 10},
        {"name": "392_ב\"ש_אילת", "distance": 240, "duration": 180, "frequency": 12},
        {"name": "380_ב\"ש_ת\"א", "distance": 110, "duration": 90, "frequency": 50},
        {"name": "470_ב\"ש_י-ם", "distance": 120, "duration": 100, "frequency": 35},
        {"name": "826_ת\"א_נצרת", "distance": 105, "duration": 95, "frequency": 25},
        {"name": "605_נתנ_ת\"א", "distance": 35, "duration": 45, "frequency": 60},
        {"name": "347_ת\"א_כ\"ס", "distance": 25, "duration": 40, "frequency": 45},
        {"name": "66_פ\"ת_ת\"א", "distance": 15, "duration": 35, "frequency": 80},
        {"name": "82_פ\"ת_ת\"א", "distance": 14, "duration": 30, "frequency": 75},
        {"name": "1_ת\"א_בת-ים", "distance": 12, "duration": 40, "frequency": 150},
        {"name": "25_ת\"א_חולון", "distance": 10, "duration": 35, "frequency": 90},
        {"name": "5_ת\"א_מרכז", "distance": 8, "duration": 25, "frequency": 200},
        {"name": "18_י-ם", "distance": 12, "duration": 45, "frequency": 130},
        {"name": "15_י-ם", "distance": 10, "duration": 35, "frequency": 100},
        {"name": "71_י-ם", "distance": 15, "duration": 50, "frequency": 80},
        {"name": "72_י-ם", "distance": 16, "duration": 55, "frequency": 85},
        {"name": "14_חיפה", "distance": 12, "duration": 30, "frequency": 60},
        {"name": "19_חיפה", "distance": 14, "duration": 35, "frequency": 55},
        {"name": "274_רחובות", "distance": 30, "duration": 55, "frequency": 40},
        {"name": "301_אשקלון", "distance": 55, "duration": 70, "frequency": 35},
        {"name": "438_י-ם_אשד", "distance": 65, "duration": 75, "frequency": 20},
        {"name": "348_אשד_ב\"ש", "distance": 60, "duration": 65, "frequency": 25},
        {"name": "112_טבריה", "distance": 25, "duration": 40, "frequency": 15}
    ]

    def format_buses_for_display(buses_list):
        df = pd.DataFrame(buses_list)
        df = df.rename(columns={
            "name": "שם הקו",
            "distance": "מרחק (ק״מ)",
            "duration": "זמן נסיעה (דקות)",
            "frequency": "תדירות (נסיעות ביום)"
        })
        return df

    st.subheader("🌍 מסד נתונים ארצי")
    st.markdown(f"**במערכת נטענו כעת {len(nationwide_buses)} קווים בפריסה ארצית.**")

    st.subheader("📋 קווים זמינים (לפני מיון)")
    st.dataframe(format_buses_for_display(nationwide_buses), use_container_width=True)

    st.divider()

    st.subheader("⚡ מיון מואץ-חומרה")
    sort_options = {
        "מרחק": "distance",
        "זמן נסיעה": "duration",
        "תדירות": "frequency",
        "שם הקו": "name"
    }

    selected_label = st.selectbox("בחר מדד למיון הקווים:", list(sort_options.keys()))
    sort_method = sort_options[selected_label]

    if st.button("מיין באמצעות מנוע C", type="primary", key="btn_sort"):
        with st.spinner('ניגש לזיכרון ה-Shared Object...'):
            try:
                if sort_method == "name":
                    sorted_buses = bus_wrapper.sort_bus_lines_by_name(nationwide_buses)
                else:
                    sorted_buses = bus_wrapper.sort_bus_lines_by_metric(nationwide_buses, sort_method)
                
                st.success(f"המיון עבר בהצלחה לפי {selected_label} במהירות שיא!")
                st.dataframe(format_buses_for_display(sorted_buses), use_container_width=True)
                
                if sort_method != "name":
                    st.subheader(f"📊 תצוגה גרפית: {selected_label}")
                    chart_data = {bus["name"]: bus[sort_method] for bus in sorted_buses}
                    st.bar_chart(chart_data)
                    
            except Exception as e:
                st.error(f"שגיאה במהלך המיון: {e}")

# ----------------------------------------------------------------------
# TAB 2: GAMES & REWARDS
# ----------------------------------------------------------------------
with tab2:
    st.header("🎮 משחק הזיכרון - צבור נקודות!")
    
    # Wallet & Progress Bar
    col_metric1, col_metric2 = st.columns(2)
    with col_metric1:
        st.metric("Moovit Coins 🪙", f"{st.session_state.moovit_coins} / 1000")
    with col_metric2:
        st.metric("משחקים שוחקו היום", f"{st.session_state.games_played_today} / 5")
        
    progress = min(st.session_state.moovit_coins / 1000.0, 1.0)
    st.progress(progress, text="התקדמות לפרס הגדול")
    
    # Grand Prize Check
    if st.session_state.moovit_coins >= 1000:
        st.balloons()
        st.success("🎉 זכית בנסיעה בינעירונית חינם (עד 40 ק\"מ)! קופון: HUJI-FREE-RIDE")
        if st.button("אפס נקודות והתחל מחדש", key="reset_points"):
            st.session_state.moovit_coins = 0
            st.session_state.games_played_today = 0
            st.rerun()
            
    st.divider()
    
    # Game Logic Check
    if all(st.session_state.matched):
        if not st.session_state.game_won_awarded:
            if st.session_state.games_played_today < 5:
                st.session_state.moovit_coins += 50
                st.session_state.games_played_today += 1
            st.session_state.game_won_awarded = True
            st.rerun() # Force rerun to update wallet immediately visually
            
        st.success("כל הכבוד! מצאת את כל הזוגות.")
        if st.session_state.games_played_today >= 5:
            st.warning("הגעת למכסת המשחקים היומית (5). לא יתווספו נקודות נוספות למשחק זה.")
            
        if st.button("שחק שוב", key="play_again"):
            init_game()
            st.rerun()
    
    st.markdown("##### מצא את זוגות הקווים התואמים:")
    # Render Game Board (4 columns by 3 rows)
    for row in range(3):
        cols = st.columns(4)
        for col_idx in range(4):
            i = row * 4 + col_idx
            with cols[col_idx]:
                if st.session_state.matched[i]:
                    # Matched card (Disabled and Shows Name)
                    st.button(f"✅\n{st.session_state.board[i]}", key=f"card_{i}", disabled=True, use_container_width=True)
                elif st.session_state.flipped[i]:
                    # Currently flipped card (Disabled to prevent re-click, Shows Name)
                    st.button(f"🚌\n{st.session_state.board[i]}", key=f"card_{i}", disabled=True, use_container_width=True)
                else:
                    # Unflipped card (Active button)
                    st.button("❓", key=f"card_{i}", on_click=flip_card, args=(i,), use_container_width=True)
