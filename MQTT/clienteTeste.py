#!/usr/bin/env python3

"""
Este exemplo se conecta ao servidor MQTT do IFSC,
faz SUBSCRIPTION para o tópico "schailay" com o callback "schai_callback",
faz PUBLISH de 4 valores,
aguarda 5 segundos,
faz UNSUBSCRIBE,
aguarda 5 segundos,
desconecta do servidor
"""

from MQTT import MqttClient
import time

mqtt = MqttClient(host='mqtt.sj.ifsc.edu.br', port=1883)
mqtt.connect()

print("Cliente conectado")

def schai_callback(topicName, msg):
	print("\n###### Recebeu ######")
	print("Tópico: {}".format(topicName))
	print("Mensagem: {}".format(msg))

mqtt.subscribe("schailay", schai_callback)

print("\nSetando os valores")
mqtt.publish("schailay", '1')
time.sleep(1)
mqtt.publish("schailay", '0')
time.sleep(1)
mqtt.publish("schailay", '1')
time.sleep(1)
mqtt.publish("schailay", '0')

print("\nAguardando 5 segundos antes do UNSUBSCRIBE")
time.sleep(5)

mqtt.unsubscribe("schailay")

print("\nAguardando 5 segundos antes do DISCONNECT")
time.sleep(5)
mqtt.disconnect()