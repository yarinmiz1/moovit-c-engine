import sys
import time
import bus_wrapper

def slow_print(text, delay=0.03):
    """Prints text slowly to the terminal for a hacker aesthetic."""
    for char in text:
        sys.stdout.write(char)
        sys.stdout.flush()
        time.sleep(delay)
    print()

def main():
    slow_print("INITIATING SECURE CONNECTION...", 0.05)
    time.sleep(1)
    slow_print("WARNING: ROGUE AI DETECTED IN HEBREW UNIVERSITY TRANSIT SERVERS.", 0.05)
    slow_print("BEIT SHEMESH <-> JERUSALEM GRID OFFLINE.")
    time.sleep(1)
    slow_print("YOUR MISSION: UTILIZE C-ENGINE TO BYPASS FIREWALLS AND RESTORE ROUTES.\n")
    time.sleep(1)

    # Hardcoded 'corrupted' dummy buses
    # Names are kept under 21 bytes to respect the C struct limits.
    corrupted_buses = [
        {"name": "X_Delta", "distance": 80, "duration": 45, "frequency": 7},
        {"name": "A_Alpha", "distance": 15, "duration": 10, "frequency": 3},
        {"name": "M_Sigma", "distance": 40, "duration": 25, "frequency": 1},
        {"name": "Z_Omega", "distance": 99, "duration": 60, "frequency": 9},
        {"name": "C_Gamma", "distance": 22, "duration": 15, "frequency": 4}
    ]

    current_buses = corrupted_buses

    # Stage 1: Firewall Bypass (Sort by name)
    slow_print("--- STAGE 1: FIREWALL BYPASS ---")
    slow_print("The firewall is scrambling route identifiers.")
    slow_print("Command required: Sort buses by 'name' to align the signature.")
    while True:
        cmd = input("Enter sort command (e.g., 'sort name'): ").strip().lower()
        if cmd == 'sort name':
            slow_print("Executing C-Engine Bubble Sort...", 0.04)
            try:
                current_buses = bus_wrapper.sort_bus_lines_by_name(current_buses)
                slow_print("SUCCESS: FIREWALL BYPASSED. Identifiers aligned.\n")
                time.sleep(1)
                break
            except Exception as e:
                slow_print(f"CRITICAL ERROR: {e}")
                return
        else:
            slow_print("ACCESS DENIED. Incorrect command. Try again.")

    # Stage 2: GPS Recalibration (Sort by distance)
    slow_print("--- STAGE 2: GPS RECALIBRATION ---")
    slow_print("The rogue AI has randomized route lengths.")
    slow_print("Command required: Sort buses by 'distance' to recalibrate GPS nodes.")
    while True:
        cmd = input("Enter sort command (e.g., 'sort distance'): ").strip().lower()
        if cmd == 'sort distance':
            slow_print("Executing C-Engine Quick Sort...", 0.04)
            try:
                current_buses = bus_wrapper.sort_bus_lines_by_metric(current_buses, 'distance')
                slow_print("SUCCESS: GPS RECALIBRATED. Distance matrix stabilized.\n")
                time.sleep(1)
                break
            except Exception as e:
                slow_print(f"CRITICAL ERROR: {e}")
                return
        else:
            slow_print("ACCESS DENIED. Incorrect command. Try again.")

    # Stage 3: Passcode Extraction (Sort by frequency)
    slow_print("--- STAGE 3: PASSCODE EXTRACTION ---")
    slow_print("Mainframe access requires a master override passcode.")
    slow_print("Command required: Sort buses by 'frequency' to reveal the code.")
    while True:
        cmd = input("Enter sort command (e.g., 'sort frequency'): ").strip().lower()
        if cmd == 'sort frequency':
            slow_print("Executing C-Engine Quick Sort...", 0.04)
            try:
                current_buses = bus_wrapper.sort_bus_lines_by_metric(current_buses, 'frequency')
                
                # Extract the frequencies to form the passcode
                passcode = "".join(str(bus['frequency']) for bus in current_buses)
                
                slow_print("SUCCESS: EXTRACTION COMPLETE.")
                time.sleep(1)
                slow_print("DECRYPTING...", 0.1)
                slow_print(f"\n*** MASTER OVERRIDE PASSCODE: {passcode} ***", 0.08)
                break
            except Exception as e:
                slow_print(f"CRITICAL ERROR: {e}")
                return
        else:
            slow_print("ACCESS DENIED. Incorrect command. Try again.")

    print()
    time.sleep(1)
    slow_print("OVERRIDE ACCEPTED.")
    slow_print("SYSTEM RESTORED. BEIT SHEMESH <-> JERUSALEM GRID ONLINE.")
    slow_print("GOOD JOB, STUDENT.")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nCONNECTION TERMINATED.")
