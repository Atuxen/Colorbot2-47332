import json, ssl, time
import paho.mqtt.client as mqtt

import queue
import uuid
import secrets_mqtt as mqtt_conf



class HiveMQ:
    def __init__(self, host, port, user, pwd):
        self.client = mqtt.Client(client_id="colab-tool")
        self.client.username_pw_set(user, pwd)
        self.client.tls_set(cert_reqs=ssl.CERT_NONE)   # skip-verify, matches ESP32
        self.client.tls_insecure_set(True)
    
        self.client.connect(host, port, keepalive=60)


    def start(self, subs=None):
        if subs:
            for t in subs: self.client.subscribe(t, qos=1)
        self.client.loop_start()

    def publish(self, topic, obj):
        self.client.publish(topic, json.dumps(obj), qos=1)


def request_task(task, timeout=8):
    req_id = str(uuid.uuid4())
    result_q = queue.Queue()

    def on_connect(client, userdata, flags, rc):
        client.subscribe(mqtt_conf.TOPIC_DATA)

    def on_message(client, userdata, msg):
        try:
            d = json.loads(msg.payload)
            if d.get("req_id") == req_id:
                result_q.put(d)  # Put the whole response
        except Exception as e:
            print("Parse error:", e)

    client = mqtt.Client()
    client.username_pw_set(mqtt_conf.USERNAME, mqtt_conf.PASSWORD)
    client.on_connect = on_connect
    client.on_message = on_message
    client.tls_set(cert_reqs=ssl.CERT_NONE)
    client.tls_insecure_set(True)

    client.connect(mqtt_conf.BROKER_HOST, mqtt_conf.PORT)
    client.loop_start()

    # Wait for connection
    connected = False
    for _ in range(40):
        if client.is_connected():
            connected = True
            break
        time.sleep(0.1)
    if not connected:
        print("Could not connect to MQTT broker.")
        client.loop_stop()
        return None

    # If the task is a dict, convert to string (for "Mix" etc)
    if isinstance(task, dict):
        task_payload = json.dumps(task)
    else:
        task_payload = task  # e.g. "Meas"

    print(f"Sending request with request id: {req_id}")
    client.publish(mqtt_conf.TOPIC_CMD, json.dumps({
        "task": task_payload,
        "req_id": req_id
    }))

    try:
        response = result_q.get(timeout=timeout)
        return response  # full dict, may have "color_sense" or "status"
    except queue.Empty:
        print("Timeout waiting for response.")
        return None
    finally:
        client.disconnect()
        client.loop_stop()