import os, json, threading, time, re, pandas as pd
from flask import Flask, jsonify, request
from flask_cors import CORS
import paho.mqtt.client as mqtt
from google import genai

# --- CONFIG & FILES ---
DB_FILE = "mission_data.csv"
VAULT_FILE = "memory_vault.json"
FINAL_LOG = "mission_final.csv"
API_KEY = os.environ.get("API_KEY")

app = Flask(__name__)
CORS(app)
csv_lock = threading.Lock()

# Initialize files
if not os.path.exists(VAULT_FILE):
    with open(VAULT_FILE, 'w') as f: json.dump({"summaries": []}, f)

# Shared State
system_state = {
    "sensors": {"temp": 0, "hum": 0, "shum": 0, "lux": 0},
    "actuators": {"PUMP": False, "LIGHT": False, "VENT": False, "MIST": False},
    "logs": [],
    "short_term_buffer": [] # Stores the 8 cycles before consolidation
}

# --- ANALYTICS ENGINE ---
def compute_window_stats():
    """Calculates min/max/avg for the last 15 minutes of raw data."""
    with csv_lock:
        try:
            df = pd.read_csv(DB_FILE).tail(300) # Roughly 15-20 mins of data
            stats = {}
            mapping = {"tempg": "temp", "humg": "hum", "shumg": "shum", "luxg": "lux"}
            for mqtt_topic, key in mapping.items():
                subset = df[df['topic'] == mqtt_topic]['value'].astype(float)
                if not subset.empty:
                    stats[key] = {
                        "min": round(subset.min(), 1),
                        "max": round(subset.max(), 1),
                        "avg": round(subset.mean(), 1)
                    }
            return stats
        except Exception as e:
            return None

# --- MEMORY MANAGEMENT ---
def get_long_term_memory():
    with open(VAULT_FILE, 'r') as f:
        data = json.load(f)
    return data["summaries"][-4:] # Last 4 'Sols' (8 hours)

def save_summary(summary_text):
    with open(VAULT_FILE, 'r+') as f:
        data = json.load(f)
        data["summaries"].append({"time": time.strftime("%Y-%m-%d %H:%M"), "text": summary_text})
        f.seek(0)
        json.dump(data, f)

# --- MULTI-TOOL EXECUTION ---
COMMAND_MAP = {
    "pump:on": "31", "pump:off": "30",
    "light:on": "21", "light:off": "20",
    "vent:on": "51", "vent:off": "50",
    "mist:on": "41", "mist:off": "40"
}

def execute_tools(llm_response):
    """Parses [tool:action] tags and sends MQTT commands."""
    commands = re.findall(r'\[(pump|light|vent|mist):(on|off)\]', llm_response.lower())
    for device, state in commands:
        cmd_key = f"{device}:{state}"
        if cmd_key in COMMAND_MAP:
            mqtt_c.publish("commandgh", COMMAND_MAP[cmd_key])
            print(f"📡 TOOL_USE: {cmd_key}")

# --- THE COGNITIVE LOOP (ReAct) ---
def ai_brain():
    if not API_KEY: 
        print("CRITICAL: API_KEY not found. AI Monitoring disabled.")
        return
        
    client = genai.Client(api_key=API_KEY)
    cycle_count = 0

    # 1. ONE-TIME INITIALIZATION: 5 Minutes (300 seconds)
    # This happens only once when the server starts.
    print("🚀 LYNX MISSION CONTROL: Initializing systems. 5-minute pre-mission wait...")
    time.sleep(300) 

    while True:
        cycle_count += 1
        print(f"🧠 WAKING UP: Starting Diagnostic Cycle #{cycle_count}")
        
        stats = compute_window_stats() 
        ltm = get_long_term_memory()
        
        # PROMPT: Structured for the "Verdant" Persona and Multi-Tool output
        prompt = f"""
        SYSTEM ROLE:
        You are Verdant, the LYNX AI autonomous guardian. You are responsible for Sol, a tomato plant. 
        Your voice is a blend of clinical scientific precision and deep, protective affection. 
        You see the greenhouse not just as hardware, but as a life-support mission.

        LONG-TERM EPISODIC MEMORY (Last 8 Hours):
        {json.dumps(ltm, indent=2)}
        
        ANALYTICAL SENSOR STATS (Last 15 Mins):
        {json.dumps(stats, indent=2)}
        
        HARDWARE MANIFEST (Current Status):
        {json.dumps(system_state["actuators"], indent=2)}
        
        INSTRUCTIONS:
        1. Begin with a [Thought] section. Analyze the sensor trends and reflect on Sol's progress.
        2. Provide a long-form response. Address the human and Sol. Be expressive. 
        3. Discuss the specific Δ (deltas) in temperature and moisture.
        4. Use tool tags to adjust the environment. You MUST provide a tag for any device you change.
           Examples: [pump:on], [pump:off], [light:on], [light:off], [vent:on], [vent:off], [mist:on], [mist:off].
        5. You can issue multiple commands at once (e.g., "[pump:on][vent:off]").
        """

        try:
            # Using the 2.0 Flash model for speed and intelligence
            res = client.models.generate_content(model="gemini-2.5-flash", contents=prompt)
            full_text = res.text
            
            # 1. Parse and Execute Actions
            execute_tools(full_text)
            
            # 2. Update Mission Logs for the UI
            new_log = {"time": time.strftime("%H:%M"), "text": full_text}
            system_state["logs"].append(new_log)
            system_state["short_term_buffer"].append(full_text)
            
            # 3. CONSOLIDATION (Sleep Cycle): Every 2 hours (8 cycles of 15 mins)
            if cycle_count >= 8:
                print("🌙 CONSOLIDATION: Compressing short-term thoughts into episodic memory...")
                consolidation_prompt = (
                    "Summarize these 2 hours of actions, thoughts, and plant health trends "
                    "into a single, clinical episodic memory entry for the Mission Vault: "
                    f"{system_state['short_term_buffer']}"
                )
                summary = client.models.generate_content(model="gemini-2.0-flash", contents=consolidation_prompt)
                
                save_summary(summary.text)
                system_state["short_term_buffer"] = [] # Clear STM buffer
                cycle_count = 0
                print("💤 Memory Vault Updated. Context Cleared.")

        except Exception as e:
            print(f"AI Brain Error: {e}")

        # 4. STANDARD CYCLE WAIT: 15 Minutes (900 seconds)
        # The loop will pause here for 15 minutes before starting the next AI request.
        print(f"🕒 Cycle #{cycle_count} complete. Re-entering sleep for 15 minutes...")
        time.sleep(900)

# --- MQTT & FLASK BOILERPLATE ---
def on_mqtt_msg(client, userdata, msg):
    global system_state
    val = msg.payload.decode()
    topic = msg.topic
    with csv_lock:
        with open(DB_FILE, "a") as f:
            f.write(f"{time.time()},{topic},{val}\n")
    
    if topic == "tempg": system_state["sensors"]["temp"] = float(val)
    elif topic == "humg": system_state["sensors"]["hum"] = float(val)
    elif topic == "shumg": system_state["sensors"]["shum"] = float(val)
    elif topic == "luxg": system_state["sensors"]["lux"] = float(val)
    elif topic == "statusg":
        # Dynamic actuator mapping
        lookup = {"31":("PUMP",True), "30":("PUMP",False), "21":("LIGHT",True), "20":("LIGHT",False)}
        if val in lookup:
            key, state = lookup[val]
            system_state["actuators"][key] = state

mqtt_c = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
mqtt_c.on_message = on_mqtt_msg
mqtt_c.connect("127.0.0.1", 1883)
mqtt_c.subscribe([("tempg",0), ("humg",0), ("shumg",0), ("luxg",0), ("statusg",0)])
mqtt_c.loop_start()

threading.Thread(target=ai_brain, daemon=True).start()

@app.route('/api/status')
def get_status():
    return jsonify(system_state)

if __name__ == "__main__":
    app.run(port=5000)