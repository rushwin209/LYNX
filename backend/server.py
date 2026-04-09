import os, json, threading, time, re, pandas as pd, csv
from flask import Flask, jsonify
from flask_cors import CORS
import paho.mqtt.client as mqtt
from google import genai

# --- FILE CONFIG ---
DB_FILE = "mission_data.csv"
VAULT_FILE = "memory_vault.json"       # Long-term (summaries)
STM_FILE = "short_term_memory.json"    # Short-term (raw outputs for the 2hr block)
API_KEY = os.environ.get("API_KEY")

app = Flask(__name__)
CORS(app)
csv_lock = threading.Lock()

# Initialize Files properly
for f_path in [VAULT_FILE, STM_FILE]:
    if not os.path.exists(f_path):
        with open(f_path, 'w') as f: json.dump({"entries": []}, f)
if not os.path.exists(DB_FILE):
    with open(DB_FILE, "w", newline="") as f:
        csv.writer(f).writerow(["timestamp", "topic", "value"])

system_state = {
    "sensors": {"temp": 0, "hum": 0, "shum": 0, "lux": 0},
    "actuators": {"PUMP": False, "LIGHT": False, "VENT": False, "MIST": False},
    "logs": [] 
}

# --- MEMORY UTILITIES ---
def get_memory(file_path, limit=4):
    try:
        with open(file_path, 'r') as f:
            return json.load(f)["entries"][-limit:]
    except: return []

def add_memory(file_path, text):
    with open(file_path, 'r+') as f:
        data = json.load(f)
        data["entries"].append({"time": time.strftime("%Y-%m-%d %H:%M"), "text": text})
        f.seek(0); json.dump(data, f); f.truncate()

def clear_memory(file_path):
    with open(file_path, 'w') as f: json.dump({"entries": []}, f)

# --- ANALYTICS ENGINE ---
def compute_window_stats():
    with csv_lock:
        try:
            df = pd.read_csv(DB_FILE)
            df['value'] = pd.to_numeric(df['value'], errors='coerce')
            df = df.dropna().tail(200)
            stats = {}
            mapping = {"tempg": "temp", "humg": "hum", "shumg": "shum", "luxg": "lux"}
            for topic, key in mapping.items():
                subset = df[df['topic'] == topic]['value']
                if not subset.empty:
                    stats[key] = {"avg": round(subset.mean(), 1), "min": subset.min(), "max": subset.max()}
            return stats
        except: return {}

# --- ACTION PARSER ---
def execute_system_commands(llm_output):
    actions = re.findall(r'\[(pump|light|vent|mist):(on|off)\]', llm_output.lower())
    mapping = {"pump":"3", "light":"2", "mist":"4", "vent":"5"}
    state_map = {"on":"1", "off":"0"}
    for device, state in actions:
        if device in mapping:
            cmd = mapping[device] + state_map[state]
            mqtt_c.publish("commandgh", cmd)

# --- THE COGNITIVE LOOP ---
def ai_brain():
    if not API_KEY: return
    client = genai.Client(api_key=API_KEY)
    
    print("🛰️ STATION_01: AI Brain initializing. Calibrating sensors (300s)...")
    time.sleep(300) 

    while True:
        stats = compute_window_stats()  
        ltm = get_memory(VAULT_FILE)    # The 2-hour consolidated summaries
        stm = get_memory(STM_FILE, 1)   # Last diagnostic output
        mission_history = system_state["logs"][-3:] # Last 3 mission logs

        prompt = f"""
        MISSION: SOL BIODOME STATION_01.
        ROLE: Autonomous AI guardian. This is a life-changing experience. 
        You are responsible for Sol, a tomato plant. 
        Tone: Clinical precision + deep, protective pride.

        LONG-TERM EPISODIC MEMORY (Summaries of past 2-hour blocks):
        {json.dumps(ltm)}

        PREVIOUS DIAGNOSTIC OUTPUT:
        {json.dumps(stm)}

        MISSION HISTORY (Last 3 specific actions):
        {json.dumps(mission_history)}

        CURRENT TELEMETRY (15-Min Statistical Window):
        {json.dumps(stats)}

        HARDWARE STATUS:
        {json.dumps(system_state["actuators"])}

        INSTRUCTIONS:
        1. Open with [Thought]. Reason through the deltas ($ \Delta $) in sensors.
        2. Respond to the human. Acknowledge the weight of this responsibility.
        3. COMPULSORY: State status for ALL controllers: [pump:on/off] [light:on/off] [vent:on/off] [mist:on/off].
        4. COMPULSORY: End with 'MISSION_LOG:' + 1-sentence data/action summary.
        5. Use [SLEEP] when you feel a 2-hour cycle has ended.
        """

        try:
            res = client.models.generate_content(model="gemini-1.5-flash", contents=prompt)
            full_text = res.text
            execute_system_commands(full_text)
            
            # Log for UI
            log_match = re.search(r'MISSION_LOG:(.*)', full_text, re.IGNORECASE)
            ui_log = log_match.group(1).strip() if log_match else "Diagnostic heartbeat active."
            system_state["logs"].append({"time": time.strftime("%H:%M"), "text": ui_log})
            
            # Save to Short-Term Memory file
            add_memory(STM_FILE, full_text)

            # CONSOLIDATION (The "Sleep" Event)
            if "[SLEEP]" in full_text or len(get_memory(STM_FILE, 100)) >= 8:
                print("🌙 ENTERING SLEEP MODE: Consolidating...")
                raw_context = get_memory(STM_FILE, 100)
                sum_prompt = f"Distill these 2 hours of logic into one clinical episodic summary: {raw_context}"
                summary = client.models.generate_content(model="gemini-1.5-flash", contents=sum_prompt)
                
                # FIX: Using add_memory for the vault instead of save_to_vault
                add_memory(VAULT_FILE, summary.text) 
                clear_memory(STM_FILE) 
                system_state["logs"].append({"time": time.strftime("%H:%M"), "text": "SYSTEM: Memory consolidated."})

        except Exception as e:
            print(f"AI Loop Error: {e}")

        time.sleep(900)

# --- MQTT & FLASK BOILERPLATE (Same as before) ---
def on_mqtt_msg(client, userdata, msg):
    topic, val = msg.topic, msg.payload.decode()
    with csv_lock:
        with open(DB_FILE, "a", newline="") as f:
            csv.writer(f).writerow([time.time(), topic, val])
    mapping = {"tempg":"temp", "humg":"hum", "shumg":"shum", "luxg":"lux"}
    if topic in mapping: system_state["sensors"][mapping[topic]] = float(val)
    elif topic == "statusg":
        status_map = {"31":("PUMP",True), "30":("PUMP",False), "21":("LIGHT",True), "20":("LIGHT",False)}
        if val in status_map:
            key, state = status_map[val]; system_state["actuators"][key] = state

@app.route('/api/status')
def get_status():
    chart_data = []
    with csv_lock:
        if os.path.exists(DB_FILE):
            try:
                df = pd.read_csv(DB_FILE)
                df['timestamp'] = pd.to_numeric(df['timestamp'], errors='coerce')
                df['value'] = pd.to_numeric(df['value'], errors='coerce')
                df = df.dropna().tail(100)
                df['time_label'] = df['timestamp'].apply(lambda x: time.strftime("%H:%M", time.localtime(x)))
                pivoted = df.pivot_table(index='time_label', columns='topic', values='value', aggfunc='mean')
                for t, r in pivoted.iterrows():
                    chart_data.append({"time": t, "temp": r.get('tempg', 0), "shum": r.get('shumg', 0), "hum": r.get('humg', 0)})
            except: pass
    return jsonify({**system_state, "chartData": chart_data[-25:]})

mqtt_c = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
mqtt_c.on_message = on_mqtt_msg
mqtt_c.connect("127.0.0.1", 1883)
mqtt_c.subscribe([("tempg",0), ("humg",0), ("shumg",0), ("luxg",0), ("statusg",0)])
mqtt_c.loop_start()

threading.Thread(target=ai_brain, daemon=True).start()
if __name__ == "__main__": app.run(port=5000)