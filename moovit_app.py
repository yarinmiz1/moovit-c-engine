import os
import subprocess
import random
import time
import streamlit as st
import pandas as pd
from geopy.geocoders import Nominatim
from geopy.distance import geodesic
import folium
from streamlit_folium import st_folium

# ======================================================================
# CRITICAL CLOUD INIT: Compile the C library BEFORE importing the wrapper
# ======================================================================
SO_FILE = "libsortbus.so"
C_FILE = "sort_bus_lines.c"

# Check if we are running on a fresh Streamlit Cloud container
if not os.path.exists(SO_FILE):
    st.info("מבצע אתחול שרת ראשוני למערכת...")
    try:
        # Run the exact GCC command to compile the shared library
        subprocess.run(
            ["gcc", "-shared", "-o", SO_FILE, "-fPIC", C_FILE],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        st.success("אתחול שרת הושלם בהצלחה!")
    except subprocess.CalledProcessError as e:
        st.error(f"שגיאת שרת.\nError: {e.stderr.decode('utf-8')}")
        st.stop()
    except FileNotFoundError:
        st.error("שגיאת מערכת - רכיב חסר.")
        st.stop()

# Now it is completely safe to import the wrapper, as libsortbus.so is guaranteed to exist
import bus_wrapper

# ======================================================================
# SESSION STATE INIT (GAMES & REWARDS & REACTIVITY FIX)
# ======================================================================
if 'moovit_coins' not in st.session_state: st.session_state.moovit_coins = 0

# Reactivity State Managers
if 'search_results_buses' not in st.session_state: st.session_state.search_results_buses = None
if 'global_sort_results' not in st.session_state: st.session_state.global_sort_results = None
if 'selected_map_route' not in st.session_state: st.session_state.selected_map_route = None
if 'map_search_msg' not in st.session_state: st.session_state.map_search_msg = ""
if 'map_search_err' not in st.session_state: st.session_state.map_search_err = ""

# --- GAME 1: MEMORY MATCH ---
def init_memory_game():
    BUS_PAIRS = [
        "415 בי\"ש - י-ם",
        "615 ת\"א - נתניה",
        "1 חיפה - קריות",
        "480 ת\"א - י-ם",
        "390 ת\"א - אילת",
        "18 ירושלים"
    ]
    cards = BUS_PAIRS * 2
    random.shuffle(cards)
    st.session_state.mem_board = cards
    st.session_state.mem_flipped = [False] * 12
    st.session_state.mem_matched = [False] * 12
    st.session_state.mem_first_flip = None
    st.session_state.mem_second_flip = None
    st.session_state.mem_game_won = False

if 'mem_board' not in st.session_state:
    init_memory_game()

def flip_mem_card(i):
    if st.session_state.mem_matched[i] or st.session_state.mem_flipped[i]:
        return
    if st.session_state.mem_first_flip is not None and st.session_state.mem_second_flip is not None:
        st.session_state.mem_flipped[st.session_state.mem_first_flip] = False
        st.session_state.mem_flipped[st.session_state.mem_second_flip] = False
        st.session_state.mem_first_flip = None
        st.session_state.mem_second_flip = None

    if st.session_state.mem_first_flip is None:
        st.session_state.mem_first_flip = i
        st.session_state.mem_flipped[i] = True
    elif st.session_state.mem_second_flip is None:
        st.session_state.mem_second_flip = i
        st.session_state.mem_flipped[i] = True
        if st.session_state.mem_board[st.session_state.mem_first_flip] == st.session_state.mem_board[st.session_state.mem_second_flip]:
            st.session_state.mem_matched[st.session_state.mem_first_flip] = True
            st.session_state.mem_matched[st.session_state.mem_second_flip] = True
            st.session_state.mem_first_flip = None
            st.session_state.mem_second_flip = None

# --- GAME 2: SIMON SAYS ---
COLORS = ['🔴', '🔵', '🟢', '🟡']
if 'simon_seq' not in st.session_state:
    st.session_state.simon_seq = []
if 'simon_user_idx' not in st.session_state:
    st.session_state.simon_user_idx = 0
if 'simon_status' not in st.session_state:
    st.session_state.simon_status = 'idle'

def start_simon():
    st.session_state.simon_seq = [random.choice(COLORS)]
    st.session_state.simon_user_idx = 0
    st.session_state.simon_status = 'showing'

def simon_click(color):
    if st.session_state.simon_status != 'playing':
        return
    idx = st.session_state.simon_user_idx
    if color == st.session_state.simon_seq[idx]:
        st.session_state.simon_user_idx += 1
        if st.session_state.simon_user_idx == len(st.session_state.simon_seq):
            st.session_state.moovit_coins += 10
            st.session_state.simon_seq.append(random.choice(COLORS))
            st.session_state.simon_user_idx = 0
            st.session_state.simon_status = 'showing'
    else:
        st.session_state.simon_status = 'lost'

# --- GAME 3: TRIVIA ---
TRIVIA_QUESTIONS = [
    {"q": "איזו חברת אוטובוסים מפעילה את הקווים העירוניים בירושלים?", "options": ["אגד", "דן", "סופרבוס", "אקסטרה"], "answer": "אקסטרה"},
    {"q": "מה המרחק המשוער מתל אביב לאילת באוטובוס?", "options": ["200 ק\"מ", "350 ק\"מ", "500 ק\"מ", "150 ק\"מ"], "answer": "350 ק\"מ"},
    {"q": "באיזו עיר נמצאת תחנת מרכזית המפרץ?", "options": ["תל אביב", "חיפה", "באר שבע", "אשדוד"], "answer": "חיפה"},
    {"q": "איך קוראים לכרטיס החכם לתשלום בתחבורה ציבורית בישראל?", "options": ["אוייסטר", "רב-קו", "מטרוקארד", "סמארט-פס"], "answer": "רב-קו"}
]
if 'trivia_idx' not in st.session_state:
    st.session_state.trivia_idx = 0

# --- GAME 4: LUGGAGE BALANCE ---
def init_luggage():
    st.session_state.luggage_unassigned = [
        {"name": "מזוודה ענקית", "w": 20},
        {"name": "עגלת תינוק", "w": 15},
        {"name": "תיק גב גדול", "w": 5},
        {"name": "ארגז כלים", "w": 10},
        {"name": "מזוודת טרולי", "w": 10}
    ]
    st.session_state.luggage_left = []
    st.session_state.luggage_right = []
    st.session_state.luggage_won = False

if 'luggage_unassigned' not in st.session_state:
    init_luggage()

def move_luggage(item, direction):
    if item in st.session_state.luggage_unassigned:
        st.session_state.luggage_unassigned.remove(item)
    elif item in st.session_state.luggage_left:
        st.session_state.luggage_left.remove(item)
    elif item in st.session_state.luggage_right:
        st.session_state.luggage_right.remove(item)
        
    if direction == 'left':
        st.session_state.luggage_left.append(item)
    elif direction == 'right':
        st.session_state.luggage_right.append(item)
    else:
        st.session_state.luggage_unassigned.append(item)

# --- GAME 5: WORDLE ---
WORDLE_WORDS = ["נתניה", "עפולה", "טבריה", "רעננה", "אשדוד"]
if 'wordle_target' not in st.session_state:
    st.session_state.wordle_target = random.choice(WORDLE_WORDS)
    st.session_state.wordle_guesses = []
    st.session_state.wordle_won = False

# --- GAME 6: IDLE TYCOON ---
if 'tycoon_multiplier' not in st.session_state:
    st.session_state.tycoon_multiplier = 1

def click_tycoon():
    st.session_state.moovit_coins += st.session_state.tycoon_multiplier

def buy_tycoon_upgrade():
    cost = st.session_state.tycoon_multiplier * 50
    if st.session_state.moovit_coins >= cost:
        st.session_state.moovit_coins -= cost
        st.session_state.tycoon_multiplier += 1


# ======================================================================
# STREAMLIT UI - HEBREW RTL & MODERN CSS
# ======================================================================
st.set_page_config(page_title="Moovit ישראל", layout="centered")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Heebo:wght@400;700&display=swap');

.stApp {
    font-family: 'Heebo', sans-serif !important;
    direction: rtl !important;
    text-align: right !important;
    background-color: #f7f9fa;
}

.stMarkdown, p, h1, h2, h3, h4, h5, h6, .stSelectbox label {
    direction: rtl !important;
    text-align: right !important;
}

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

.stButton>button:disabled {
    background-color: #f0f2f6 !important;
    color: #31333F !important;
    opacity: 1 !important;
    transform: none !important;
    box-shadow: none !important;
}

[data-testid="stDataFrame"] {
    direction: rtl !important;
    background-color: white;
    border-radius: 12px;
    padding: 10px;
    box-shadow: 0 2px 8px rgba(0,0,0,0.05);
}

.wordle-box {
    display: inline-block;
    width: 45px;
    height: 45px;
    line-height: 45px;
    text-align: center;
    font-size: 22px;
    font-weight: bold;
    margin: 3px;
    border-radius: 6px;
    color: white;
}
</style>
""", unsafe_allow_html=True)

st.title("🚌 Moovit ישראל - תכנון מסלולים חכם")

tab1, tab2 = st.tabs(["🚏 חיפוש מסלולים", "🎮 הטבות ומשחקים"])

# ----------------------------------------------------------------------
# TAB 1: ROUTE SORTING & PLANNING
# ----------------------------------------------------------------------
with tab1:
    st.markdown("ברוכים הבאים למערכת תכנון המסלולים המתקדמת בישראל. חפשו מסלולים ישירים או משולבים כולל הצגה חיה על המפה.")

    # ======================================================================
    # EXPANDED NATIONWIDE DATABASE WITH DICTIONARY STATIONS & COORDS
    # SECURITY NOTE: The "name" field remains strictly <= 20 bytes (UTF-8)
    # ======================================================================
    nationwide_buses = [
        {
            "name": "480_Jeru_TA", "display_name": "480 - תל אביב - ירושלים",
            "distance": 65, "duration": 60, "frequency": 120,
            "stations": [
                {"name": "תל אביב סבידור מרכז", "lat": 32.0835, "lon": 34.7981},
                {"name": "מסוף ארלוזורוב", "lat": 32.0825, "lon": 34.7960},
                {"name": "מחלף חמד", "lat": 31.8023, "lon": 35.1275},
                {"name": "ירושלים תחנה מרכזית", "lat": 31.7895, "lon": 35.2023}
            ]
        },
        {
            "name": "405_Jeru_TA", "display_name": "405 - תל אביב - ירושלים",
            "distance": 63, "duration": 55, "frequency": 110,
            "stations": [
                {"name": "תל אביב תחנה מרכזית חדשה", "lat": 32.0560, "lon": 34.7800},
                {"name": "מחלף חמד", "lat": 31.8023, "lon": 35.1275},
                {"name": "ירושלים תחנה מרכזית", "lat": 31.7895, "lon": 35.2023}
            ]
        },
        {
            "name": "415_BS_Jeru", "display_name": "415 - בית שמש - ירושלים",
            "distance": 35, "duration": 45, "frequency": 50,
            "stations": [
                {"name": "בית שמש תחנת רכבת", "lat": 31.7586, "lon": 34.9860},
                {"name": "מסוף רמת בית שמש", "lat": 31.7208, "lon": 34.9854},
                {"name": "צומת שמשון", "lat": 31.7766, "lon": 35.0113},
                {"name": "ירושלים תחנה מרכזית", "lat": 31.7895, "lon": 35.2023}
            ]
        },
        {
            "name": "947_Haifa_Jeru", "display_name": "947 - חיפה - ירושלים",
            "distance": 150, "duration": 180, "frequency": 30,
            "stations": [
                {"name": "מרכזית חוף הכרמל", "lat": 32.7930, "lon": 34.9570},
                {"name": "מחלף נתניה", "lat": 32.3021, "lon": 34.8631},
                {"name": "מחלף חמד", "lat": 31.8023, "lon": 35.1275},
                {"name": "ירושלים תחנה מרכזית", "lat": 31.7895, "lon": 35.2023}
            ]
        },
        {
            "name": "910_Haifa_TA", "display_name": "910 - חיפה - תל אביב",
            "distance": 95, "duration": 90, "frequency": 40,
            "stations": [
                {"name": "מרכזית חוף הכרמל", "lat": 32.7930, "lon": 34.9570},
                {"name": "תל אביב סבידור מרכז", "lat": 32.0835, "lon": 34.7981},
                {"name": "תל אביב תחנה מרכזית חדשה", "lat": 32.0560, "lon": 34.7800}
            ]
        },
        {
            "name": "390_TA_Eilat", "display_name": "390 - תל אביב - אילת",
            "distance": 350, "duration": 270, "frequency": 15,
            "stations": [
                {"name": "תל אביב תחנה מרכזית חדשה", "lat": 32.0560, "lon": 34.7800},
                {"name": "באר שבע תחנה מרכזית", "lat": 31.2430, "lon": 34.7970},
                {"name": "צומת הערבה", "lat": 30.8030, "lon": 35.3050},
                {"name": "אילת תחנה מרכזית", "lat": 29.5540, "lon": 34.9540}
            ]
        },
        {
            "name": "444_Jeru_Eilat", "display_name": "444 - ירושלים - אילת",
            "distance": 320, "duration": 260, "frequency": 10,
            "stations": [
                {"name": "ירושלים תחנה מרכזית", "lat": 31.7895, "lon": 35.2023},
                {"name": "צומת הערבה", "lat": 30.8030, "lon": 35.3050},
                {"name": "אילת תחנה מרכזית", "lat": 29.5540, "lon": 34.9540}
            ]
        },
        {
            "name": "392_BS_Eilat", "display_name": "392 - באר שבע - אילת",
            "distance": 240, "duration": 180, "frequency": 12,
            "stations": [
                {"name": "באר שבע תחנה מרכזית", "lat": 31.2430, "lon": 34.7970},
                {"name": "מצפה רמון", "lat": 30.6080, "lon": 34.8030},
                {"name": "אילת תחנה מרכזית", "lat": 29.5540, "lon": 34.9540}
            ]
        },
        {
            "name": "380_BS_TA", "display_name": "380 - באר שבע - תל אביב",
            "distance": 110, "duration": 90, "frequency": 50,
            "stations": [
                {"name": "באר שבע תחנה מרכזית", "lat": 31.2430, "lon": 34.7970},
                {"name": "אוניברסיטת בן גוריון", "lat": 31.2610, "lon": 34.8010},
                {"name": "תל אביב סבידור מרכז", "lat": 32.0835, "lon": 34.7981}
            ]
        },
        {
            "name": "470_BS_Jeru", "display_name": "470 - באר שבע - ירושלים",
            "distance": 120, "duration": 100, "frequency": 35,
            "stations": [
                {"name": "באר שבע תחנה מרכזית", "lat": 31.2430, "lon": 34.7970},
                {"name": "קרית גת", "lat": 31.6030, "lon": 34.7700},
                {"name": "ירושלים תחנה מרכזית", "lat": 31.7895, "lon": 35.2023}
            ]
        },
        {
            "name": "826_TA_Nazareth", "display_name": "826 - תל אביב - נצרת",
            "distance": 105, "duration": 95, "frequency": 25,
            "stations": [
                {"name": "תל אביב תחנה מרכזית חדשה", "lat": 32.0560, "lon": 34.7800},
                {"name": "תל אביב סבידור מרכז", "lat": 32.0835, "lon": 34.7981},
                {"name": "צומת יקנעם", "lat": 32.6560, "lon": 35.1050},
                {"name": "נצרת מרכז", "lat": 32.7010, "lon": 35.2930}
            ]
        },
        {
            "name": "605_Netanya_TA", "display_name": "605 - נתניה - תל אביב",
            "distance": 35, "duration": 45, "frequency": 60,
            "stations": [
                {"name": "נתניה תחנה מרכזית", "lat": 32.3270, "lon": 34.8560},
                {"name": "מחלף פולג", "lat": 32.2680, "lon": 34.8460},
                {"name": "תל אביב סבידור מרכז", "lat": 32.0835, "lon": 34.7981},
                {"name": "תל אביב תחנה מרכזית חדשה", "lat": 32.0560, "lon": 34.7800}
            ]
        },
        {
            "name": "347_TA_KS", "display_name": "347 - תל אביב - כפר סבא",
            "distance": 25, "duration": 40, "frequency": 45,
            "stations": [
                {"name": "תל אביב תחנה מרכזית חדשה", "lat": 32.0560, "lon": 34.7800},
                {"name": "תל אביב סבידור מרכז", "lat": 32.0835, "lon": 34.7981},
                {"name": "כפר סבא תחנה מרכזית", "lat": 32.1740, "lon": 34.9070}
            ]
        },
        {
            "name": "66_PT_TA", "display_name": "66 - פתח תקווה - תל אביב",
            "distance": 15, "duration": 35, "frequency": 80,
            "stations": [
                {"name": "פתח תקווה תחנה מרכזית", "lat": 32.0930, "lon": 34.8820},
                {"name": "בית חולים בילינסון", "lat": 32.0890, "lon": 34.8620},
                {"name": "רמת גן קניון איילון", "lat": 32.0990, "lon": 34.8250},
                {"name": "תל אביב דיזנגוף סנטר", "lat": 32.0780, "lon": 34.7740}
            ]
        },
        {
            "name": "82_PT_TA", "display_name": "82 - פתח תקווה - תל אביב",
            "distance": 14, "duration": 30, "frequency": 75,
            "stations": [
                {"name": "פתח תקווה תחנה מרכזית", "lat": 32.0930, "lon": 34.8820},
                {"name": "ציר ז'בוטינסקי בני ברק", "lat": 32.0880, "lon": 34.8360},
                {"name": "תל אביב סבידור מרכז", "lat": 32.0835, "lon": 34.7981}
            ]
        },
        {
            "name": "1_TA_BatYam", "display_name": "1 - תל אביב - בת ים",
            "distance": 12, "duration": 40, "frequency": 150,
            "stations": [
                {"name": "בת ים יוספטל", "lat": 32.0150, "lon": 34.7500},
                {"name": "יפו העתיקה", "lat": 32.0520, "lon": 34.7530},
                {"name": "תל אביב סבידור מרכז", "lat": 32.0835, "lon": 34.7981},
                {"name": "פתח תקווה תחנה מרכזית", "lat": 32.0930, "lon": 34.8820}
            ]
        },
        {
            "name": "25_TA_Holon", "display_name": "25 - תל אביב - חולון",
            "distance": 10, "duration": 35, "frequency": 90,
            "stations": [
                {"name": "חולון קוגל", "lat": 32.0250, "lon": 34.7800},
                {"name": "תל אביב יפו", "lat": 32.0520, "lon": 34.7530},
                {"name": "אוניברסיטת ת\"א", "lat": 32.1130, "lon": 34.8040}
            ]
        },
        {
            "name": "5_TA", "display_name": "5 - תל אביב רכבת מרכז",
            "distance": 8, "duration": 25, "frequency": 200,
            "stations": [
                {"name": "תל אביב סבידור מרכז", "lat": 32.0835, "lon": 34.7981},
                {"name": "תל אביב דיזנגוף סנטר", "lat": 32.0780, "lon": 34.7740},
                {"name": "תל אביב תחנה מרכזית חדשה", "lat": 32.0560, "lon": 34.7800}
            ]
        },
        {
            "name": "18_Jeru", "display_name": "18 - ירושלים",
            "distance": 12, "duration": 45, "frequency": 130,
            "stations": [
                {"name": "ירושלים מלחה", "lat": 31.7490, "lon": 35.1870},
                {"name": "ירושלים מרכז העיר", "lat": 31.7820, "lon": 35.2150},
                {"name": "ירושלים תחנה מרכזית", "lat": 31.7895, "lon": 35.2023}
            ]
        },
        {
            "name": "71_Jeru", "display_name": "71 - ירושלים",
            "distance": 15, "duration": 50, "frequency": 80,
            "stations": [
                {"name": "ירושלים גילה", "lat": 31.7250, "lon": 35.1860},
                {"name": "ירושלים תחנה מרכזית", "lat": 31.7895, "lon": 35.2023},
                {"name": "ירושלים רמות", "lat": 31.8150, "lon": 35.1850}
            ]
        },
        {
            "name": "14_Haifa", "display_name": "14 - חיפה",
            "distance": 12, "duration": 30, "frequency": 60,
            "stations": [
                {"name": "חיפה בת גלים", "lat": 32.8330, "lon": 34.9810},
                {"name": "חיפה טכניון", "lat": 32.7760, "lon": 35.0230}
            ]
        },
        {
            "name": "274_Rehovot_TA", "display_name": "274 - רחובות - תל אביב",
            "distance": 30, "duration": 55, "frequency": 40,
            "stations": [
                {"name": "רחובות תחנה מרכזית", "lat": 31.8920, "lon": 34.8110},
                {"name": "ראשון לציון מרכז", "lat": 31.9640, "lon": 34.8040},
                {"name": "תל אביב סבידור מרכז", "lat": 32.0835, "lon": 34.7981},
                {"name": "אוניברסיטת ת\"א", "lat": 32.1130, "lon": 34.8040}
            ]
        },
        {
            "name": "301_Ashkelon_TA", "display_name": "301 - אשקלון - תל אביב",
            "distance": 55, "duration": 70, "frequency": 35,
            "stations": [
                {"name": "אשקלון תחנה מרכזית", "lat": 31.6740, "lon": 34.5740},
                {"name": "אשדוד תחנה מרכזית", "lat": 31.7920, "lon": 34.6380},
                {"name": "ראשון לציון מרכז", "lat": 31.9640, "lon": 34.8040},
                {"name": "תל אביב תחנה מרכזית חדשה", "lat": 32.0560, "lon": 34.7800}
            ]
        },
        {
            "name": "438_Jeru_Ashdod", "display_name": "438 - ירושלים - אשדוד",
            "distance": 65, "duration": 75, "frequency": 20,
            "stations": [
                {"name": "אשדוד תחנה מרכזית", "lat": 31.7920, "lon": 34.6380},
                {"name": "מחלף חמד", "lat": 31.8023, "lon": 35.1275},
                {"name": "ירושלים תחנה מרכזית", "lat": 31.7895, "lon": 35.2023}
            ]
        },
        {
            "name": "348_Ashdod_BS", "display_name": "348 - אשדוד - באר שבע",
            "distance": 60, "duration": 65, "frequency": 25,
            "stations": [
                {"name": "אשדוד תחנה מרכזית", "lat": 31.7920, "lon": 34.6380},
                {"name": "קרית גת", "lat": 31.6030, "lon": 34.7700},
                {"name": "באר שבע תחנה מרכזית", "lat": 31.2430, "lon": 34.7970}
            ]
        },
        {
            "name": "112_Tiberias", "display_name": "112 - טבריה",
            "distance": 25, "duration": 40, "frequency": 15,
            "stations": [
                {"name": "טבריה תחנה מרכזית", "lat": 32.7880, "lon": 35.5310},
                {"name": "צומת גולני", "lat": 32.7760, "lon": 35.4050},
                {"name": "טבריה שיכון ד", "lat": 32.7950, "lon": 35.5180}
            ]
        },
        {
            "name": "68_Jeru_Scopus", "display_name": "68 - ירושלים הר הצופים",
            "distance": 8, "duration": 30, "frequency": 150,
            "stations": [
                {"name": "ירושלים תחנה מרכזית", "lat": 31.7895, "lon": 35.2023},
                {"name": "ירושלים מרכז העיר", "lat": 31.7820, "lon": 35.2150},
                {"name": "האוניברסיטה העברית הר הצופים", "lat": 31.7942, "lon": 35.2447}
            ]
        }
    ]

    def format_buses_for_display(buses_list):
        display_list = []
        for b in buses_list:
            display_list.append({
                "שם הקו": b.get("display_name", b["name"]),
                "מרחק (ק״מ)": b["distance"],
                "זמן נסיעה (דקות)": b["duration"],
                "תדירות (נסיעות)": b["frequency"]
            })
        return pd.DataFrame(display_list)

    def render_route_map(stations_list):
        valid_coords = [(s["lat"], s["lon"]) for s in stations_list if "lat" in s and "lon" in s]
        
        if valid_coords:
            center_lat = sum(c[0] for c in valid_coords) / len(valid_coords)
            center_lon = sum(c[1] for c in valid_coords) / len(valid_coords)
            zoom = 11
        else:
            center_lat, center_lon = 31.5, 34.75
            zoom = 8

        m = folium.Map(location=[center_lat, center_lon], zoom_start=zoom)
        folium.PolyLine(valid_coords, color="#ff6a00", weight=5, opacity=0.8).add_to(m)
        
        if len(valid_coords) >= 2:
            # Origin
            folium.Marker(valid_coords[0], tooltip=f"מוצא: {stations_list[0]['name']}", icon=folium.Icon(color="green")).add_to(m)
            # Destination
            folium.Marker(valid_coords[-1], tooltip=f"יעד: {stations_list[-1]['name']}", icon=folium.Icon(color="red")).add_to(m)
            
            # Intermediates
            for i in range(1, len(valid_coords) - 1):
                is_transfer = "החלפה" in stations_list[i]['name']
                col = "orange" if is_transfer else "#ff6a00"
                folium.CircleMarker(valid_coords[i], radius=7 if is_transfer else 5, color=col, fill=True, tooltip=stations_list[i]['name']).add_to(m)
        
        return m

    def get_closest_station(address):
        geolocator = Nominatim(user_agent="moovit_c_engine_app_agent")
        try:
            location = geolocator.geocode(address + ", ישראל", timeout=3)
            if location:
                user_coord = (location.latitude, location.longitude)
                closest_station = None
                min_dist = float('inf')
                
                for bus in nationwide_buses:
                    for s in bus["stations"]:
                        dist = geodesic(user_coord, (s["lat"], s["lon"])).km
                        if dist < min_dist:
                            min_dist = dist
                            closest_station = s["name"]
                return closest_station
        except:
            return None
        return None

    # ----------------------------------------------------------------------
    # FEATURE 1: GEO-TRIP PLANNER (ORIGIN -> DEST WITH TRANSFERS)
    # ----------------------------------------------------------------------
    st.subheader("🗺️ תכנון נסיעה (חיפוש כתובת או תחנה)")
    
    all_station_names = set()
    for bus in nationwide_buses:
        for s in bus["stations"]:
            all_station_names.add(s["name"])
    all_station_names = sorted(list(all_station_names))
    
    col_addr, col_drop = st.columns(2)
    with col_addr:
        st.markdown("**חיפוש חכם לפי כתובת:**")
        addr_origin = st.text_input("כתובת מוצא:")
        addr_dest = st.text_input("כתובת יעד:")
    with col_drop:
        st.markdown("**בחירה ידנית מתחנות:**")
        drop_origin = st.selectbox("או בחר תחנת מוצא:", ["- בחר -"] + all_station_names)
        drop_dest = st.selectbox("או בחר תחנת יעד:", ["- בחר -"] + all_station_names)

    if st.button("חפש מסלול", type="primary", use_container_width=True):
        origin_st_name, dest_st_name = None, None
        
        with st.spinner("מאתר מיקומים גיאוגרפיים..."):
            if addr_origin:
                origin_st_name = get_closest_station(addr_origin)
                if origin_st_name: st.success(f"נמצאה תחנת מוצא קרובה: {origin_st_name}")
                else: st.session_state.map_search_err = "לא הצלחנו לאתר את כתובת המוצא."
            elif drop_origin != "- בחר -":
                origin_st_name = drop_origin
                
            if addr_dest:
                dest_st_name = get_closest_station(addr_dest)
                if dest_st_name: st.success(f"נמצאה תחנת יעד קרובה: {dest_st_name}")
                else: st.session_state.map_search_err = "לא הצלחנו לאתר את כתובת היעד."
            elif drop_dest != "- בחר -":
                dest_st_name = drop_dest

        if origin_st_name and dest_st_name:
            if origin_st_name == dest_st_name:
                st.session_state.map_search_err = "תחנת המוצא והיעד זהות."
            else:
                st.session_state.map_search_err = ""
                direct_buses = []
                transfer_buses = []
                
                # 1. DIRECT ROUTES
                for bus in nationwide_buses:
                    names = [s["name"] for s in bus["stations"]]
                    if origin_st_name in names and dest_st_name in names:
                        if names.index(origin_st_name) < names.index(dest_st_name):
                            direct_buses.append(bus)
                
                # 2. 1-TRANSFER ROUTES
                if not direct_buses:
                    for b1 in nationwide_buses:
                        names1 = [s["name"] for s in b1["stations"]]
                        if origin_st_name in names1:
                            o_idx = names1.index(origin_st_name)
                            stations_after_o = names1[o_idx+1:]
                            
                            for b2 in nationwide_buses:
                                if b1 == b2: continue
                                names2 = [s["name"] for s in b2["stations"]]
                                if dest_st_name in names2:
                                    d_idx = names2.index(dest_st_name)
                                    stations_before_d = names2[:d_idx]
                                    
                                    # Find intersection
                                    common = set(stations_after_o).intersection(set(stations_before_d))
                                    if common:
                                        t_station_name = list(common)[0]
                                        t_idx1 = names1.index(t_station_name)
                                        t_idx2 = names2.index(t_station_name)
                                        
                                        virt_name = f"V_{b1['name'][:5]}_{b2['name'][:5]}"[:20]
                                        virt_display = f"{b1['display_name'].split(' - ')[0]} 🔄 {b2['display_name'].split(' - ')[0]} (החלפה ב{t_station_name})"
                                        
                                        t_node = {"name": f"החלפה: {t_station_name}", "lat": b1["stations"][t_idx1]["lat"], "lon": b1["stations"][t_idx1]["lon"]}
                                        combined_stations = b1["stations"][o_idx:t_idx1] + [t_node] + b2["stations"][t_idx2+1:d_idx+1]
                                        
                                        virt_bus = {
                                            "name": virt_name,
                                            "display_name": virt_display,
                                            "distance": b1["distance"] + b2["distance"],
                                            "duration": b1["duration"] + b2["duration"] + 15,
                                            "frequency": min(b1["frequency"], b2["frequency"]),
                                            "stations": combined_stations,
                                            "is_virtual": True
                                        }
                                        transfer_buses.append(virt_bus)
                
                all_found = direct_buses + transfer_buses
                if all_found:
                    st.session_state.search_results_buses = all_found
                    st.session_state.map_search_msg = f"נמצאו {len(all_found)} אפשרויות הגעה מ-{origin_st_name} אל {dest_st_name}."
                    
                    # Pre-calculate best route map so it persists
                    c_safe = [{"name": b["name"], "distance": b["distance"], "duration": b["duration"], "frequency": b["frequency"]} for b in all_found]
                    sorted_safe = bus_wrapper.sort_bus_lines_by_metric(c_safe, "duration")
                    bus_dict = {b["name"]: b for b in all_found}
                    sorted_buses = [bus_dict[s["name"]] for s in sorted_safe]
                    st.session_state.selected_map_route = sorted_buses[0]
                else:
                    st.session_state.search_results_buses = None
                    st.session_state.map_search_err = "לא נמצא מסלול המחבר בין התחנות."

    # RENDER SEARCH RESULTS FROM STATE (Fixes Reactivity Bug)
    if st.session_state.map_search_err:
        st.error(st.session_state.map_search_err)
        
    if st.session_state.search_results_buses:
        st.success(st.session_state.map_search_msg)
        
        c_safe = [{"name": b["name"], "distance": b["distance"], "duration": b["duration"], "frequency": b["frequency"]} for b in st.session_state.search_results_buses]
        sorted_safe = bus_wrapper.sort_bus_lines_by_metric(c_safe, "duration")
        bus_dict = {b["name"]: b for b in st.session_state.search_results_buses}
        sorted_buses = [bus_dict[s["name"]] for s in sorted_safe]
        
        st.dataframe(format_buses_for_display(sorted_buses), use_container_width=True)
        
        if st.session_state.selected_map_route:
            st.markdown(f"**מפה מונחית עבור המסלול המהיר ביותר ({st.session_state.selected_map_route['display_name']}):**")
            # Render map. returned_objects=[] prevents st_folium from rerunning the app when the map is clicked!
            route_map = render_route_map(st.session_state.selected_map_route["stations"])
            st_folium(route_map, width=700, height=400, returned_objects=[])
            
            st.markdown("#### פירוט התחנות המלא:")
            for idx, s in enumerate(st.session_state.selected_map_route["stations"]):
                if idx == 0: st.markdown(f"🟢 **{s['name']}**")
                elif idx == len(st.session_state.selected_map_route["stations"]) - 1: st.markdown(f"🏁 **{s['name']}**")
                else: st.markdown(f"⬇️ {s['name']}")

    st.divider()

    # ----------------------------------------------------------------------
    # FEATURE 2: GLOBAL SORTING (Powered securely by C-Engine)
    # ----------------------------------------------------------------------
    st.subheader("🌍 כלל מסד הנתונים הארצי (סינון חכם)")
    st.markdown(f"**מעודכן בזמן אמת: {len(nationwide_buses)} קווים זמינים בפריסה ארצית.**")

    sort_options = {
        "סנן לפי מרחק": "distance",
        "סנן לפי זמן נסיעה": "duration",
        "סנן לפי תדירות": "frequency",
        "סנן לפי שם הקו": "name"
    }

    selected_label = st.selectbox("בחר כיצד תרצה לסנן את המסלולים במערכת:", list(sort_options.keys()))
    sort_method = sort_options[selected_label]

    if st.button("החל סינון חכם", type="primary", key="btn_sort_global"):
        with st.spinner('מחשב את המסלולים הטובים ביותר...'):
            try:
                # SECURITY LOCK
                c_safe_buses = [
                    {
                        "name": b["name"], 
                        "distance": b["distance"], 
                        "duration": b["duration"], 
                        "frequency": b["frequency"]
                    } for b in nationwide_buses
                ]
                
                if sort_method == "name":
                    sorted_safe = bus_wrapper.sort_bus_lines_by_name(c_safe_buses)
                else:
                    sorted_safe = bus_wrapper.sort_bus_lines_by_metric(c_safe_buses, sort_method)
                
                bus_dict = {b["name"]: b for b in nationwide_buses}
                st.session_state.global_sort_results = [bus_dict[s["name"]] for s in sorted_safe]
            except Exception as e:
                st.error(f"שגיאת מערכת. אנא נסה שוב מאוחר יותר: {e}")

    # RENDER GLOBAL SORT RESULTS FROM STATE
    if st.session_state.global_sort_results:
        st.success(f"התוצאות סוננו בהצלחה.")
        st.dataframe(format_buses_for_display(st.session_state.global_sort_results), use_container_width=True)

# ----------------------------------------------------------------------
# TAB 2: GAMES & REWARDS
# ----------------------------------------------------------------------
with tab2:
    st.header("🎁 הטבות Moovit - צבור נקודות!")
    st.markdown("שחק בזמן הנסיעה, צבור נקודות בארנק הדיגיטלי, ותוכל לזכות בנסיעות חינם או בהטבות בלעדיות למשתמשי האפליקציה.")
    
    col_metric1, col_metric2 = st.columns(2)
    with col_metric1:
        st.metric("Moovit Coins 🪙", f"{st.session_state.moovit_coins} / 1000")
    with col_metric2:
        st.metric("מכפיל הקלקה (טייקון)", f"x{st.session_state.tycoon_multiplier}")
        
    progress = min(st.session_state.moovit_coins / 1000.0, 1.0)
    st.progress(progress, text="התקדמות לפרס הגדול (נסיעה חינם)")
    
    if st.session_state.moovit_coins >= 1000:
        st.balloons()
        st.success("🎉 זכית בנסיעה בינעירונית חינם (עד 40 ק\"מ)! קופון: HUJI-FREE-RIDE")
        if st.button("אפס נקודות והתחל מחדש", key="reset_points"):
            st.session_state.moovit_coins = 0
            st.rerun()
            
    st.divider()
    
    GAME_OPTIONS = [
        "1. משחק הזיכרון", 
        "2. סיימון אומר - מסלולים", 
        "3. טריוויה תחבורה", 
        "4. איזון כבודה", 
        "5. וורדל תחבורה", 
        "6. איל ההון של אגד (Idle)"
    ]
    selected_game = st.selectbox("בחר מיני-משחק להעברת הזמן:", GAME_OPTIONS)
    st.divider()

    # ==========================================
    # 1. MEMORY MATCH
    # ==========================================
    if selected_game == "1. משחק הזיכרון":
        st.subheader("משחק הזיכרון: התאם את זוגות הקווים")
        if all(st.session_state.mem_matched):
            if not st.session_state.mem_game_won:
                st.session_state.moovit_coins += 50
                st.session_state.mem_game_won = True
                st.rerun()
            st.success("כל הכבוד! מצאת את כל הזוגות (זכית ב-50 מטבעות).")
            if st.button("שחק שוב", key="mem_play_again"):
                init_memory_game()
                st.rerun()
                
        for row in range(3):
            cols = st.columns(4)
            for col_idx in range(4):
                i = row * 4 + col_idx
                with cols[col_idx]:
                    if st.session_state.mem_matched[i]:
                        st.button(f"✅\n{st.session_state.mem_board[i]}", key=f"mem_{i}", disabled=True, use_container_width=True)
                    elif st.session_state.mem_flipped[i]:
                        st.button(f"🚌\n{st.session_state.mem_board[i]}", key=f"mem_{i}", disabled=True, use_container_width=True)
                    else:
                        st.button("❓", key=f"mem_{i}", on_click=flip_mem_card, args=(i,), use_container_width=True)

    # ==========================================
    # 2. SIMON SAYS
    # ==========================================
    elif selected_game == "2. סיימון אומר - מסלולים":
        st.subheader("סיימון אומר: חזור על הרצף")
        st.markdown("שים לב: הרצף יוצג למספר שניות, לאחר מכן עליך ללחוץ על הכפתורים באותו הסדר בדיוק! מקבלים 10 נקודות על כל שלב שעוברים.")
        
        if st.session_state.simon_status == 'idle':
            if st.button("התחל משחק"):
                start_simon()
                st.rerun()
        
        elif st.session_state.simon_status == 'showing':
            ph = st.empty()
            with ph.container():
                st.write("### צפה ברצף עכשיו:")
                for color in st.session_state.simon_seq:
                    st.markdown(f"<h1 style='text-align: center; font-size: 80px;'>{color}</h1>", unsafe_allow_html=True)
                    time.sleep(0.8)
                    st.markdown("<h1 style='text-align: center; font-size: 80px;'>...</h1>", unsafe_allow_html=True)
                    time.sleep(0.2)
            ph.empty()
            st.session_state.simon_status = 'playing'
            st.rerun()
            
        elif st.session_state.simon_status == 'playing':
            st.write(f"תורך! שלב {st.session_state.simon_user_idx + 1} מתוך {len(st.session_state.simon_seq)}")
            cols = st.columns(4)
            for idx, color in enumerate(COLORS):
                with cols[idx]:
                    st.button(color, key=f"simon_btn_{idx}", on_click=simon_click, args=(color,), use_container_width=True)
                    
        elif st.session_state.simon_status == 'lost':
            st.error("טעות ברצף! המשחק נגמר.")
            st.write(f"הגעת לאורך רצף של {len(st.session_state.simon_seq) - 1}.")
            if st.button("נסה שוב"):
                st.session_state.simon_status = 'idle'
                st.rerun()

    # ==========================================
    # 3. TRIVIA
    # ==========================================
    elif selected_game == "3. טריוויה תחבורה":
        st.subheader("טריוויה: עד כמה אתה מכיר את התחבורה בישראל?")
        if st.session_state.trivia_idx < len(TRIVIA_QUESTIONS):
            q_data = TRIVIA_QUESTIONS[st.session_state.trivia_idx]
            st.write(f"**שאלה {st.session_state.trivia_idx + 1} מתוך {len(TRIVIA_QUESTIONS)}:** {q_data['q']}")
            ans = st.radio("בחר תשובה:", q_data['options'], key=f"trivia_radio_{st.session_state.trivia_idx}")
            if st.button("אישור"):
                if ans == q_data['answer']:
                    st.success("תשובה נכונה! (+10 מטבעות)")
                    st.session_state.moovit_coins += 10
                    st.session_state.trivia_idx += 1
                    time.sleep(1.5)
                    st.rerun()
                else:
                    st.error(f"תשובה שגויה. התשובה הנכונה היא: {q_data['answer']}")
                    st.session_state.trivia_idx += 1
                    time.sleep(2)
                    st.rerun()
        else:
            st.success("סיימת את כל שאלות הטריוויה הקיימות!")
            if st.button("התחל מחדש"):
                st.session_state.trivia_idx = 0
                st.rerun()

    # ==========================================
    # 4. LUGGAGE BALANCE
    # ==========================================
    elif selected_game == "4. איזון כבודה":
        st.subheader("איזון כבודה: משקל מושלם")
        st.markdown("מיין את הכבודה לצד ימין ולצד שמאל של תא המטען כך שהמשקל יהיה שווה לחלוטין בשני הצדדים.")
        
        sum_l = sum(i['w'] for i in st.session_state.luggage_left)
        sum_r = sum(i['w'] for i in st.session_state.luggage_right)
        
        if sum_l == sum_r and sum_l > 0 and len(st.session_state.luggage_unassigned) == 0:
            if not st.session_state.luggage_won:
                st.session_state.moovit_coins += 50
                st.session_state.luggage_won = True
                st.rerun()
            st.success("מעולה! תא המטען מאוזן לחלוטין (זכית ב-50 מטבעות).")
            if st.button("אפס מטען ושחק שוב"):
                init_luggage()
                st.rerun()
                
        col1, col2, col3 = st.columns(3)
        with col1:
            st.write(f"### צד שמאל ({sum_l} ק\"ג)")
            for item in st.session_state.luggage_left:
                st.button(f"⬅️ {item['name']} ({item['w']} ק\"ג)", key=f"l_{item['name']}", on_click=move_luggage, args=(item, 'unassigned'))
                
        with col2:
            st.write("### ממתינים לשיבוץ")
            for item in st.session_state.luggage_unassigned:
                c1, c2 = st.columns(2)
                with c1:
                    st.button("שמאל ⬅️", key=f"ul_{item['name']}", on_click=move_luggage, args=(item, 'left'))
                with c2:
                    st.button("➡️ ימין", key=f"ur_{item['name']}", on_click=move_luggage, args=(item, 'right'))
                st.markdown(f"<div style='text-align: center;'>{item['name']} ({item['w']} ק\"ג)</div>", unsafe_allow_html=True)
                st.divider()
                
        with col3:
            st.write(f"### צד ימין ({sum_r} ק\"ג)")
            for item in st.session_state.luggage_right:
                st.button(f"{item['name']} ({item['w']} ק\"ג) ➡️", key=f"r_{item['name']}", on_click=move_luggage, args=(item, 'unassigned'))

    # ==========================================
    # 5. TRANSIT WORDLE
    # ==========================================
    elif selected_game == "5. וורדל תחבורה":
        st.subheader("וורדל תחבורה: ערי ישראל (5 אותיות)")
        st.markdown("נחש את שם העיר (בדיוק 5 אותיות). 🟩 אות ומקום נכונים. 🟨 אות נכונה במקום שגוי.")
        
        target = st.session_state.wordle_target
        
        for g in st.session_state.wordle_guesses:
            html = ""
            for i, char in enumerate(g):
                if char == target[i]:
                    color = "#6aaa64" # Green
                elif char in target:
                    color = "#c9b458" # Yellow
                else:
                    color = "#787c7e" # Gray
                html += f"<div class='wordle-box' style='background-color: {color};'>{char}</div>"
            st.markdown(f"<div style='text-align: center; direction: rtl;'>{html}</div>", unsafe_allow_html=True)
            
        if st.session_state.wordle_won:
            st.success("הצלחת! זכית ב-50 מטבעות.")
            if st.button("שחק מחדש"):
                st.session_state.wordle_target = random.choice(WORDLE_WORDS)
                st.session_state.wordle_guesses = []
                st.session_state.wordle_won = False
                st.rerun()
        elif len(st.session_state.wordle_guesses) >= 6:
            st.error(f"המשחק נגמר. המילה הייתה: {target}")
            if st.button("שחק מחדש"):
                st.session_state.wordle_target = random.choice(WORDLE_WORDS)
                st.session_state.wordle_guesses = []
                st.session_state.wordle_won = False
                st.rerun()
        else:
            with st.form("wordle_form"):
                guess = st.text_input("הכנס ניחוש (5 אותיות):", max_chars=5)
                submit = st.form_submit_button("נחש")
                if submit:
                    if len(guess) != 5:
                        st.error("חובה להכניס בדיוק 5 אותיות.")
                    else:
                        st.session_state.wordle_guesses.append(guess)
                        if guess == target:
                            st.session_state.moovit_coins += 50
                            st.session_state.wordle_won = True
                        st.rerun()

    # ==========================================
    # 6. IDLE TYCOON
    # ==========================================
    elif selected_game == "6. איל ההון של אגד (Idle)":
        st.subheader("איל ההון של אגד (Clicker)")
        st.markdown("לחץ על האוטובוס כדי להרוויח מטבעות פסיביים. השתמש במטבעות כדי לקנות שדרוגים בחנות.")
        
        st.button(f"🚌 לחץ כאן להסעת נוסעים (+{st.session_state.tycoon_multiplier} מטבעות)", key="tycoon_click", on_click=click_tycoon, use_container_width=True)
        
        st.divider()
        st.write("### חנות שדרוגים")
        cost = st.session_state.tycoon_multiplier * 50
        st.write(f"**מנוע אוטובוס משופר** (הגדל מכפיל ב-+1). מחיר: {cost} מטבעות.")
        if st.session_state.moovit_coins >= cost:
            st.button("קנה שדרוג", on_click=buy_tycoon_upgrade)
        else:
            st.button("אין מספיק מטבעות לקנייה", disabled=True)
