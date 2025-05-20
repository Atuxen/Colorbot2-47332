import json, ssl, time
import paho.mqtt.client as mqtt

class HiveMQ:
    def __init__(self, host, port, user, pwd):
        self.client = mqtt.Client(client_id="colab-tool")
        self.client.username_pw_set(user, pwd)
        self.client.tls_set(cert_reqs=ssl.CERT_NONE)   # skip-verify, matches ESP32
        self.client.tls_insecure_set(True)
        self.client.on_message = self._on_msg
        self.client.connect(host, port, keepalive=60)

    def _on_msg(self, client, userdata, msg):
        try:
            payload = json.loads(msg.payload)
        except ValueError:
            payload = msg.payload.decode()
        print(f"REPSONSE FROM MQTT BROKER:  {msg.topic}: {payload}")

    def start(self, subs=None):
        if subs:
            for t in subs: self.client.subscribe(t, qos=1)
        self.client.loop_start()

    def publish(self, topic, obj):
        self.client.publish(topic, json.dumps(obj), qos=1)





