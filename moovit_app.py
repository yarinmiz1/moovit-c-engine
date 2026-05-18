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
# SESSION STATE INIT (GAMES & REWARDS)
# ======================================================================
if 'moovit_coins' not in st.session_state:
    st.session_state.moovit_coins = 0

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
    st.markdown("ברוכים הבאים למערכת תכנון המסלולים המתקדמת בישראל. חפשו מסלולים ישירים או משולבים כולל הצגה על המפה.")

    # ======================================================================
    # GEO-STATIONS DATABASE
    # ======================================================================
    STATIONS_COORDS = {
        "בית שמש תחנת רכבת": (31.7586, 34.9860),
        "מסוף רמת בית שמש": (31.7208, 34.9854),
        "צומת שמשון": (31.7766, 35.0113),
        "מחלף חמד": (31.8023, 35.1275),
        "ירושלים תחנה מרכזית": (31.7895, 35.2023),
        "האוניברסיטה העברית הר הצופים": (31.7942, 35.2447),
        "ירושלים מרכז העיר": (31.7820, 35.2150),
        "ירושלים מלחה": (31.7490, 35.1870),
        "ירושלים גילה": (31.7250, 35.1860),
        "ירושלים רמות": (31.8150, 35.1850),
        "תל אביב סבידור מרכז": (32.0835, 34.7981),
        "תל אביב תחנה מרכזית חדשה": (32.0560, 34.7800),
        "מסוף ארלוזורוב": (32.0825, 34.7960),
        "מחלף השלום": (32.0734, 34.7930),
        "מרכזית חוף הכרמל": (32.7930, 34.9570),
        "חיפה בת גלים": (32.8330, 34.9810),
        "חיפה טכניון": (32.7760, 35.0230),
        "באר שבע תחנה מרכזית": (31.2430, 34.7970),
        "אילת תחנה מרכזית": (29.5540, 34.9540),
        "צומת הערבה": (30.8030, 35.3050),
        "DEFAULT": (31.5000, 34.7500) # Center fallback
    }

    # ======================================================================
    # EXPANDED DATABASE WITH STATIONS
    # ======================================================================
    nationwide_buses = [
        {
            "name": "68_י-ם_פנימי", "display_name": "68 - ירושלים מרכזית להר הצופים",
            "distance": 8, "duration": 30, "frequency": 150,
            "stations": ["ירושלים תחנה מרכזית", "ירושלים מרכז העיר", "האוניברסיטה העברית הר הצופים"]
        },
        {
            "name": "480_ת\"א_י-ם", "display_name": "480 - תל אביב - ירושלים",
            "distance": 65, "duration": 60, "frequency": 120,
            "stations": ["תל אביב סבידור מרכז", "מסוף ארלוזורוב", "מחלף חמד", "ירושלים תחנה מרכזית"]
        },
        {
            "name": "405_ת\"א_י-ם", "display_name": "405 - תל אביב - ירושלים",
            "distance": 63, "duration": 55, "frequency": 110,
            "stations": ["תל אביב תחנה מרכזית חדשה", "מחלף חמד", "ירושלים תחנה מרכזית"]
        },
        {
            "name": "415_בי\"ש_י-ם", "display_name": "415 - בית שמש - ירושלים",
            "distance": 35, "duration": 45, "frequency": 50,
            "stations": ["בית שמש תחנת רכבת", "מסוף רמת בית שמש", "צומת שמשון", "ירושלים תחנה מרכזית"]
        },
        {
            "name": "947_חיפה_י-ם", "display_name": "947 - חיפה - ירושלים",
            "distance": 150, "duration": 180, "frequency": 30,
            "stations": ["מרכזית חוף הכרמל", "מחלף חמד", "ירושלים תחנה מרכזית"]
        },
        {
            "name": "910_חיפה_ת\"א", "display_name": "910 - חיפה - תל אביב",
            "distance": 95, "duration": 90, "frequency": 40,
            "stations": ["מרכזית חוף הכרמל", "תל אביב סבידור מרכז", "תל אביב תחנה מרכזית חדשה"]
        },
        {
            "name": "390_ת\"א_אילת", "display_name": "390 - תל אביב - אילת",
            "distance": 350, "duration": 270, "frequency": 15,
            "stations": ["תל אביב תחנה מרכזית חדשה", "באר שבע תחנה מרכזית", "צומת הערבה", "אילת תחנה מרכזית"]
        },
        {
            "name": "444_י-ם_אילת", "display_name": "444 - ירושלים - אילת",
            "distance": 320, "duration": 260, "frequency": 10,
            "stations": ["ירושלים תחנה מרכזית", "צומת הערבה", "אילת תחנה מרכזית"]
        },
        {
            "name": "392_ב\"ש_אילת", "display_name": "392 - באר שבע - אילת",
            "distance": 240, "duration": 180, "frequency": 12,
            "stations": ["באר שבע תחנה מרכזית", "אילת תחנה מרכזית"]
        },
        {
            "name": "380_ב\"ש_ת\"א", "display_name": "380 - באר שבע - תל אביב",
            "distance": 110, "duration": 90, "frequency": 50,
            "stations": ["באר שבע תחנה מרכזית", "תל אביב סבידור מרכז"]
        },
        {
            "name": "470_ב\"ש_י-ם", "display_name": "470 - באר שבע - ירושלים",
            "distance": 120, "duration": 100, "frequency": 35,
            "stations": ["באר שבע תחנה מרכזית", "ירושלים תחנה מרכזית"]
        },
        {
            "name": "826_ת\"א_נצרת", "display_name": "826 - תל אביב - נצרת",
            "distance": 105, "duration": 95, "frequency": 25,
            "stations": ["תל אביב תחנה מרכזית חדשה", "תל אביב סבידור מרכז"]
        },
        {
            "name": "18_י-ם", "display_name": "18 - ירושלים מלחה",
            "distance": 12, "duration": 45, "frequency": 130,
            "stations": ["ירושלים מלחה", "ירושלים מרכז העיר", "ירושלים תחנה מרכזית"]
        },
        {
            "name": "71_י-ם", "display_name": "71 - ירושלים גילה לרמות",
            "distance": 15, "duration": 50, "frequency": 80,
            "stations": ["ירושלים גילה", "ירושלים תחנה מרכזית", "ירושלים רמות"]
        },
        {
            "name": "14_חיפה", "display_name": "14 - חיפה",
            "distance": 12, "duration": 30, "frequency": 60,
            "stations": ["חיפה בת גלים", "חיפה טכניון"]
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
        coords = [STATIONS_COORDS.get(s, STATIONS_COORDS["DEFAULT"]) for s in stations_list]
        valid_coords = [c for c in coords if c != STATIONS_COORDS["DEFAULT"]]
        
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
            folium.Marker(valid_coords[0], tooltip=f"מוצא: {stations_list[0]}", icon=folium.Icon(color="green")).add_to(m)
            folium.Marker(valid_coords[-1], tooltip=f"יעד: {stations_list[-1]}", icon=folium.Icon(color="red")).add_to(m)
            
            for i in range(1, len(valid_coords) - 1):
                folium.CircleMarker(valid_coords[i], radius=6, color="#ff6a00", fill=True, tooltip=stations_list[i]).add_to(m)
        
        return m

    def get_closest_station(address):
        geolocator = Nominatim(user_agent="moovit_c_engine_app_agent")
        try:
            location = geolocator.geocode(address + ", ישראל", timeout=3)
            if location:
                user_coord = (location.latitude, location.longitude)
                closest_station = None
                min_dist = float('inf')
                for station, coord in STATIONS_COORDS.items():
                    if station != "DEFAULT":
                        dist = geodesic(user_coord, coord).km
                        if dist < min_dist:
                            min_dist = dist
                            closest_station = station
                return closest_station
        except:
            return None
        return None

    # ----------------------------------------------------------------------
    # FEATURE 1: GEO-TRIP PLANNER (ORIGIN -> DEST WITH TRANSFERS)
    # ----------------------------------------------------------------------
    st.subheader("🗺️ תכנון נסיעה (חיפוש כתובת או תחנה)")
    
    all_stations = set()
    for bus in nationwide_buses:
        all_stations.update(bus["stations"])
    all_stations = sorted(list(all_stations))
    
    col_addr, col_drop = st.columns(2)
    with col_addr:
        st.markdown("**חיפוש חכם לפי כתובת:**")
        addr_origin = st.text_input("כתובת מוצא:")
        addr_dest = st.text_input("כתובת יעד:")
    with col_drop:
        st.markdown("**בחירה ידנית מתחנות:**")
        drop_origin = st.selectbox("או בחר תחנת מוצא:", ["- בחר -"] + all_stations)
        drop_dest = st.selectbox("או בחר תחנת יעד:", ["- בחר -"] + all_stations)

    if st.button("חפש מסלול", type="primary", use_container_width=True):
        origin_st, dest_st = None, None
        
        with st.spinner("מאתר מיקומים גיאוגרפיים..."):
            if addr_origin:
                origin_st = get_closest_station(addr_origin)
                if origin_st: st.success(f"נמצאה תחנת מוצא קרובה: {origin_st}")
                else: st.error("לא הצלחנו לאתר את כתובת המוצא. אנא בחר מהרשימה.")
            elif drop_origin != "- בחר -":
                origin_st = drop_origin
                
            if addr_dest:
                dest_st = get_closest_station(addr_dest)
                if dest_st: st.success(f"נמצאה תחנת יעד קרובה: {dest_st}")
                else: st.error("לא הצלחנו לאתר את כתובת היעד. אנא בחר מהרשימה.")
            elif drop_dest != "- בחר -":
                dest_st = drop_dest

        if origin_st and dest_st:
            if origin_st == dest_st:
                st.warning("תחנת המוצא והיעד זהות. אתה כבר ביעד!")
            else:
                st.markdown(f"### מסלולים עבור: **{origin_st}** ⬅️ **{dest_st}**")
                direct_buses = []
                transfer_buses = []
                
                # 1. DIRECT ROUTES
                for bus in nationwide_buses:
                    if origin_st in bus["stations"] and dest_st in bus["stations"]:
                        if bus["stations"].index(origin_st) < bus["stations"].index(dest_st):
                            direct_buses.append(bus)
                
                # 2. 1-TRANSFER ROUTES
                if not direct_buses:
                    for b1 in nationwide_buses:
                        if origin_st in b1["stations"]:
                            o_idx = b1["stations"].index(origin_st)
                            stations_after_o = b1["stations"][o_idx+1:]
                            
                            for b2 in nationwide_buses:
                                if b1 == b2: continue
                                if dest_st in b2["stations"]:
                                    d_idx = b2["stations"].index(dest_st)
                                    stations_before_d = b2["stations"][:d_idx]
                                    
                                    # Find intersection
                                    common = set(stations_after_o).intersection(set(stations_before_d))
                                    if common:
                                        t_station = list(common)[0]
                                        # CREATE VIRTUAL BUS FOR C-ENGINE
                                        virt_name = f"V_{b1['name'][:5]}_{b2['name'][:5]}"[:20]
                                        virt_display = f"{b1['display_name'].split(' - ')[0]} 🔄 {b2['display_name'].split(' - ')[0]} (החלפה ב{t_station})"
                                        
                                        t_idx1 = b1["stations"].index(t_station)
                                        t_idx2 = b2["stations"].index(t_station)
                                        combined_stations = b1["stations"][o_idx:t_idx1] + [f"החלפה: {t_station}"] + b2["stations"][t_idx2+1:d_idx+1]
                                        
                                        virt_bus = {
                                            "name": virt_name,
                                            "display_name": virt_display,
                                            "distance": b1["distance"] + b2["distance"],
                                            "duration": b1["duration"] + b2["duration"] + 15, # 15 min transfer penalty
                                            "frequency": min(b1["frequency"], b2["frequency"]),
                                            "stations": combined_stations,
                                            "is_virtual": True
                                        }
                                        transfer_buses.append(virt_bus)
                
                all_found_buses = direct_buses + transfer_buses
                
                if all_found_buses:
                    st.success(f"נמצאו {len(all_found_buses)} אפשרויות הגעה.")
                    
                    # RUN THROUGH C-ENGINE FOR SORTING
                    c_safe_buses = [{"name": b["name"], "distance": b["distance"], "duration": b["duration"], "frequency": b["frequency"]} for b in all_found_buses]
                    sorted_safe = bus_wrapper.sort_bus_lines_by_metric(c_safe_buses, "duration")
                    bus_dict = {b["name"]: b for b in all_found_buses}
                    sorted_buses = [bus_dict[s["name"]] for s in sorted_safe]
                    
                    st.dataframe(format_buses_for_display(sorted_buses), use_container_width=True)
                    
                    # RENDER MAP FOR BEST ROUTE
                    best_route = sorted_buses[0]
                    st.markdown(f"**מפה עבור המסלול המהיר ביותר ({best_route['display_name']}):**")
                    # Clean out 'החלפה:' strings for geocoding
                    clean_stations = [s.replace("החלפה: ", "") for s in best_route["stations"]]
                    route_map = render_route_map(clean_stations)
                    st_folium(route_map, width=700, height=400)
                    
                else:
                    st.error("לא נמצא מסלול המחבר בין התחנות, גם לא עם החלפה אחת.")

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
                sorted_buses = [bus_dict[s["name"]] for s in sorted_safe]
                
                st.success(f"התוצאות סוננו בהצלחה לפי דרישתך.")
                st.dataframe(format_buses_for_display(sorted_buses), use_container_width=True)
            except Exception as e:
                st.error(f"שגיאת מערכת. אנא נסה שוב מאוחר יותר: {e}")


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
