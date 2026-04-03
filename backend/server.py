import os, json, threading, time, pandas as pd
from flask import Flask, jsonify, request
from flask_cors import CORS
import paho.mqtt.client as mqtt
from google import genai

app = Flask(__name__)
CORS(app)

DB_FILE = "mission_data.csv"
# Ensure CSV has headers if it's new
if not os.path.exists(DB_FILE):
    pd.DataFrame(columns=["timestamp", "topic", "value"]).to_csv(DB_FILE, index=False)

# Shared State for UI
system_state = {
    "sensors": {"temp": 0, "hum": 0, "shum": 0, "lux": 0},
    "actuators": {"PUMP": False, "LIGHT": False, "VENT": False, "MIST": False},
    "logs": []
}

def on_mqtt_msg(client, userdata, msg):
    global system_state
    val = msg.payload.decode()
    topic = msg.topic
    
    # 1. Log to CSV for AI History
    new_entry = pd.DataFrame([[time.time(), topic, val]], columns=["timestamp", "topic", "value"])
    new_entry.to_csv(DB_FILE, mode='a', header=False, index=False)

    # 2. Update Live UI State
    if topic == "tempg": system_state["sensors"]["temp"] = float(val)
    elif topic == "humg": system_state["sensors"]["hum"] = float(val)
    elif topic == "shumg": system_state["sensors"]["shum"] = float(val)
    elif topic == "luxg": system_state["sensors"]["lux"] = int(val)
    elif topic == "statusg":
        mapping = {"21":("LIGHT",True), "20":("LIGHT",False), "31":("PUMP",True), "30":("PUMP",False), 
                   "51":("VENT",True), "50":("VENT",False), "41":("MIST",True), "40":("MIST",False)}
        if val in mapping:
            dev, status = mapping[val]
            system_state["actuators"][dev] = status

mqtt_c = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
mqtt_c.on_message = on_mqtt_msg
mqtt_c.connect("127.0.0.1", 1883)
mqtt_c.subscribe([("tempg",0), ("humg",0), ("shumg",0), ("luxg",0), ("statusg",0)])
threading.Thread(target=mqtt_c.loop_forever, daemon=True).start()

# AI Loop: Reads CSV to make decisions
def ai_brain():
    client = genai.Client(api_key=os.environ.get("API_KEY"))
    while True:
        time.sleep(300) # Analyze every 5 mins
        try:
            df = pd.read_csv(DB_FILE).tail(20) # Get last 20 readings
            history_summary = df.to_string()
            prompt = f"Horticultural Analysis Request. History:\n{history_summary}\nDecide next action."
            res = client.models.generate_content(model="gemini-3-flash-preview", contents=prompt)
            system_state["logs"].append({"time": time.strftime("%H:%M"), "text": res.text[:150]})
        except Exception as e: print(f"AI Error: {e}")

threading.Thread(target=ai_brain, daemon=True).start()

@app.route('/api/status')
def get_status():
    try:
        # Read the last 50 entries to build the graph
        df = pd.read_csv(DB_FILE)
        
        # We need to pivot the data so each timestamp has all variables in one row
        # for the Recharts format: [{time: 12:00, temp: 22, shum: 60}, ...]
        recent_df = df.tail(100) # Get a good window of data
        
        # Simple formatting for Recharts
        # We group by timestamp and create a list of dicts
        chart_data = []
        for ts, group in recent_df.groupby('timestamp'):
            row = {"time": time.strftime("%H:%M", time.localtime(ts))}
            for _, item in group.iterrows():
                # Map MQTT topics to chart keys
                key_map = {"tempg": "temp", "humg": "hum", "shumg": "shum", "luxg": "lux"}
                if item['topic'] in key_map:
                    row[key_map[item['topic']]] = float(item['value'])
            chart_data.append(row)

        return jsonify({
            "sensors": system_state["sensors"],
            "actuators": system_state["actuators"],
            "logs": system_state["logs"],
            "chartData": chart_data[-30:] # Send last 30 time-points to the graph
        })
    except Exception as e:
        return jsonify({"error": str(e), "sensors": system_state["sensors"], "logs": []})

@app.route('/api/cmd', methods=['POST'])
def cmd():
    mqtt_c.publish("commandgh", str(request.json['code']))
    return jsonify({"status":"ok"})

if __name__ == "__main__":
    app.run(port=5000)