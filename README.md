# Moovit C-Engine Project

## 1. החלקים שמימשנו בתרגיל
בתרגיל זה מימשנו מנוע מיון יעיל בשפת C המשמש לסידור ולניהול קווי תחבורה ציבורית. המנוע מממש אלגוריתמי מיון מתקדמים (Bubble Sort, Quick Sort) המאפשרים למיין את קווי האוטובוס על בסיס מרחק, משך נסיעה ותדירות. כדי לשלב את יעילות ה-C עם ממשק פייתון מודרני, עטפנו את הפונקציות באמצעות ספריית `ctypes` בקובץ הגישור `bus_wrapper.py`.

## 2. ההרחבות שמימשנו
- **קימפול בענן (Cloud Compilation):** אפליקציית ה-Streamlit מקמפלת באופן דינמי את קוד ה-C (באמצעות `gcc` ו-`subprocess`) באופן אוטומטי טרם עליית האפליקציה, מה שמבטיח פריסה חלקה בענן הציבורי ללא הגדרות סביבה מסובכות.
- **משחקיות ותגמולים (Gamification Arcade):** בנינו ארקייד משחקים מנוהל-State הכולל 6 מיני-משחקים (כגון Memory Match, Transit Wordle ו-Idle Tycoon). המערכת משתמשת ב-`session_state` של Streamlit כדי לאפשר צבירת "מטבעות" וקבלת קופון ל"נסיעה חינם".
- **מנוע ניתוב וקידוד גיאוגרפי (Routing Engine & Geocoding):** שילבנו את ספריית `geopy` לצורך המרת כתובות רחוב אמיתיות לקואורדינטות. בנוסף, מימשנו אלגוריתם חכם לאיתור מסלולים משולבים הכוללים החלפת קווים בתחנות חופפות.
- **מפות אינטראקטיביות (Interactive Maps):** יישמנו תצוגה חיה ויזואלית של המסלולים על גבי מפת OpenStreetMap, תוך שימוש בספריות `folium` ו-`streamlit-folium` לשרטוט התחנות והנתיב.

## 3. מבנה הקוד
- `moovit_app.py`: הקובץ המרכזי המריץ את ממשק המשתמש (Frontend), את לוגיקת הניתוב ואת מערכת המשחקים.
- `bus_wrapper.py`: גשר ה-`ctypes` המנהל את התקשורת הבטוחה בין פייתון ל-C.
- **קבצי ה-`.c` וה-`.h`:** קבצי הליבה בשפת C המכילים את אלגוריתמי המיון ומבני הנתונים (Structs) המקוריים.

## 4. כיצד להפעיל פיצ'רים מרכזיים
האפליקציה פרוסה וזמינה לשימוש ב-Streamlit Cloud.
בכדי להריץ את הפרויקט על מחשב מקומי:
1. בצעו Clone למאגר.
2. התקינו את הספריות הנדרשות בעזרת הפקודה: `pip install -r requirements.txt`.
3. הפעילו את האפליקציה בעזרת הפקודה: `streamlit run moovit_app.py`.

*שימו לב: לחיצה על כפתורי הסינון וחיפוש המסלולים בממשק מפעילה באופן שקוף וישיר את פונקציות המיון בתוך מנוע ה-C.*

## 5. כתובת הגיט
https://github.com/yarinmiz1/moovit-c-engine

---

# Moovit C-Engine Project

## 1. Core Implementation
In this assignment, we implemented an efficient C-language sorting engine used to organize and manage public transit routes. The engine implements advanced sorting algorithms (Bubble Sort, Quick Sort) that allow sorting bus lines based on distance, duration, and frequency. To combine the efficiency of C with a modern Python interface, we wrapped the functions using the `ctypes` library in the bridge file `bus_wrapper.py`.

## 2. Extensions
- **Cloud Compilation:** The Streamlit app dynamically compiles the C code (using `gcc` via `subprocess`) automatically before the app starts, ensuring seamless deployment to the public cloud without complex environment setups.
- **Gamification Arcade:** We built a state-managed arcade featuring 6 mini-games (e.g., Memory Match, Transit Wordle, and Idle Tycoon). The system uses Streamlit's `session_state` to allow accumulating "coins" and earning a "Free Ride" coupon.
- **Routing Engine & Geocoding:** We integrated the `geopy` library to convert real street addresses into coordinates. Additionally, we implemented a smart algorithm to locate combined routes involving line transfers at overlapping stations.
- **Interactive Maps:** We implemented a live visual display of the routes on an OpenStreetMap, utilizing the `folium` and `streamlit-folium` libraries to plot the stations and path.

## 3. Code Structure
- `moovit_app.py`: The main file running the user interface (Frontend), routing logic, and the games system.
- `bus_wrapper.py`: The `ctypes` bridge managing secure communication between Python and C.
- **`.c` and `.h` files:** The core files in C language containing the sorting algorithms and the original data structures (Structs).

## 4. How to Run Key Features
The app is deployed and available for use on Streamlit Cloud.
To run the project on a local machine:
1. Clone the repository.
2. Install the required libraries using the command: `pip install -r requirements.txt`.
3. Run the app using the command: `streamlit run moovit_app.py`.

*Note: Clicking the sorting and route search buttons in the interface transparently and directly triggers the sorting functions within the C engine.*

## 5. Git URL
https://github.com/yarinmiz1/moovit-c-engine
