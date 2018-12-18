#!/usr/bin/env python3

from MQTT import MqttClient
import time

mqtt = MqttClient()
mqtt.connect()

print("Cliente conectado")

mqtt.publish("schai", '1')
time.sleep(1)
mqtt.publish("schai", '0')
time.sleep(1)
mqtt.publish("schai", '1')
time.sleep(1)
mqtt.publish("schai", '0')

try:
	while True:
		pass
except KeyboardInterrupt:
	pass

if mqtt.is_connected():
	mqtt.disconnect()