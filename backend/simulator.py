import paho.mqtt.client as mqtt
import time
import random

BROKER = "127.0.0.1"
# All topics required for Sol Biodome
TOPICS = ["tempg", "humg", "shumg", "luxg", "statusg"]

# Initial Environment
state = {
    "temp": 22.0, "hum": 50.0, "shum": 60.0, "lux": 2000,
    "pump": False, "lights": False, "vent": False, "mist": False
}

def on_message(client, userdata, msg):
    payload = msg.payload.decode()
    # Handle all actuator codes
    if payload == "31": state["pump"] = True
    elif payload == "30": state["pump"] = False
    elif payload == "21": state["lights"] = True
    elif payload == "20": state["lights"] = False
    elif payload == "51": state["vent"] = True
    elif payload == "50": state["vent"] = False
    elif payload == "41": state["mist"] = True
    elif payload == "40": state["mist"] = False
    
    # Confirm back to Server/UI
    client.publish("statusg", payload)

client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
client.on_message = on_message
client.connect(BROKER, 1883)
client.subscribe("commandgh")
client.loop_start()

print("--- SOL LYNX SIMULATOR: 2-MINUTE CYCLE ---")

while True:
    # 1. Simulate Physics
    if state["pump"]: state["shum"] += 5.0
    else: state["shum"] -= 0.5
    
    if state["vent"]: state["temp"] -= 1.0
    else: state["temp"] += 0.2

    if state["mist"]: state["hum"] += 3.0
    else: state["hum"] -= 0.3

    # 2. Publish all variables
    client.publish("tempg", round(state["temp"], 2))
    client.publish("humg", round(state["hum"], 2))
    client.publish("shumg", round(state["shum"], 2))
    client.publish("luxg", random.randint(1500, 40000) if state["lights"] else 1200)

    print(f"Cycle Sync: T:{state['temp']} H:{state['hum']} S:{state['shum']}")
    time.sleep(60)