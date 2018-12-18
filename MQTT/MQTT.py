#!/usr/bin/env python3

from enum import IntEnum
import string
import random
import threading
import socket


class MqttClient:
    class ControlPacketTypes(IntEnum):
        CONNECT = 1
        CONNACK = 2
        PUBLISH = 3
        PUBACK = 4
        PUBREC = 5
        PUBREL = 6
        PUBCOMP = 7
        SUBSCRIBE = 8
        SUBACK = 9
        UNSUBSCRIBE = 10
        UNSUBACK = 11
        PINGREQ = 12
        PINGRESP = 13
        DISCONNECT = 14

    def __init__(self, host='mqtt.sj.ifsc.edu.br', port=1883):
        self.host = host
        self.port = port
        self.connected_flag = False
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._thread = None

    def _utf8encode(self, string):
        bString = string.encode('utf-8')
        tamanho = len(bString).to_bytes(2, byteorder='big')
        bString = tamanho + bString
        return bString

    def _calcularRemainingSize(self, tamanho):
        resultado = b''
        while True:
            encodedByte = tamanho % 128
            tamanho = tamanho // 128

            if (tamanho > 0):
                encodedByte = encodedByte | 128
                resultado = resultado + encodedByte.to_bytes(1, byteorder='big')
            else:
                resultado = resultado + encodedByte.to_bytes(1, byteorder='big')
                break
        return resultado

    def _montaPacoteConnect(self):
        # monta payload contendo o Client Identifier
        # string aleatória para servidr de client identifier
        client_identifier = ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(10))
        payload = self._utf8encode(client_identifier)

        #monta o variable header
        # protocol name size
        variable_header = b'\x00\x04'
        # protocol name
        variable_header = variable_header + 'MQTT'.encode('utf-8')
        #protocol level valor fixo = 4
        variable_header = variable_header + b'\x04'
        # connect flags, 00000010 = somente o Clean Session setado
        variable_header = variable_header + b'\x02'
        # bytes de keep alive, 0 = desativado
        variable_header = variable_header + b'\x00\x00'

        # fixed header
        fixed_header = (self.ControlPacketTypes.CONNECT << 4).to_bytes(1, byteorder='big')
        fixed_header = fixed_header + self._calcularRemainingSize(len(variable_header)+len(payload))

        # monta pacote completo
        pacoteCompleto = fixed_header + variable_header + payload
        return pacoteCompleto

    def _montaPacoteDisconnect(self):
        fixed_header = (self.ControlPacketTypes.DISCONNECT << 4).to_bytes(1, byteorder='big')
        fixed_header = fixed_header + b'\x00'
        return fixed_header

    def _montaPacotePublish(self, topic, msg, retain):
        # monta payload com a mensagem codificada em utf-8
        payload = msg.encode('utf-8')#self._utf8encode(msg)

        # monta variable header com o topic name,
        # o Packet Identifier não deve ser utilizado com QoS 0
        variable_header = self._utf8encode(topic)

        # monta fixed_header
        primeiro_byte = (self.ControlPacketTypes.PUBLISH << 4) | (retain << 0)
        fixed_header = primeiro_byte.to_bytes(1, byteorder='big')
        fixed_header = fixed_header + self._calcularRemainingSize(len(variable_header) + len(payload))

        # monta pacote completo
        pacoteCompleto = fixed_header + variable_header + payload
        return pacoteCompleto

    def _montaPacoteSubscribe(self, topic):
        #monta payload com o topic e com QoS 0
        payload = self._utf8encode(topic) + b'\x00'

        #monta variable header, contém o Packet Identifier
        variable_header = random.randint(0, 1024).to_bytes(2, byteorder='big')

    def _send(self, pacote):
        try:
            return self.socket.send(pacote)
        except OSError:
            print("Timeout")
            self.socket.close()
            self.connected_flag = False
            return 0

    def connect(self):
        print("Conectando...")
        self.socket.settimeout(10)
        try:
            self.socket.connect((self.host, self.port))
        except OSError:
            return False
        print("Socket conectado")
        print("Enviando MQTT Connect")

        pacoteConnect = self._montaPacoteConnect()
        sent = self._send(pacoteConnect)
        if sent == 0:
            return False

        data = self.socket.recv(8192)
        if data is None:
            print("Sem resposta do servidor")
            self.socket.close()
            return False

        if not self.handle_connect(data):
            self.socket.close()
            return False

        self._thread = threading.Thread(target=self._thread_recebe)
        self._thread.daemon = True

        self._thread.start()

        return True

    def _thread_recebe(self):
        while self.connected_flag:
            try:
                data = self.socket.recv(8192)
                self.handle_read(data)
            except socket.timeout:
                pass
        print('Encerrando _thread_read')

    def disconnect(self):
        print("Enviando MQTT Disconnect")
        pacoteDisconnect = self._montaPacoteDisconnect()
        self._send(pacoteDisconnect)
        self.connected_flag = False

    def publish(self, topic, msg, retain=True):
        pacotePublish = self._montaPacotePublish(topic, msg, retain)
        print("Enviando PUBLISH")
        print(pacotePublish)
        self._send(pacotePublish)

    def subscribe(self):
        pass

    def unsubscribe(self):
        pass

    def is_connected(self):
        return self.connected_flag

    def handle_connect(self, pacote_recebido):
        print("Pacote recebido:")
        print(pacote_recebido)

        tamanho = len(pacote_recebido)

        if tamanho < 1:
            return False

        tipoPacote = pacote_recebido[0] >> 4
        if tipoPacote == self.ControlPacketTypes.CONNACK:
            # se tamanho for diferente de 4, o pacote está mal formatado
            if tamanho != 4:
                return False
            # se byte 1 for diferente de 2, o pacote está mal formatado
            if pacote_recebido[1] != 2:
                return False
            # código de retorno = 0 significa que a conexão foi aceita
            if pacote_recebido[3] == 0:
                self.connected_flag = True
                print("Conexão aceita")
                return True
            else:
                print("Erro na conexão, resposta: {}".format(pacote_recebido[3]))
        return False

    def handle_read(self, pacote_recebido):
        print("Pacote recebido:")
        print(pacote_recebido)

        tamanho = len(pacote_recebido)

        if tamanho < 1:
            return

        """
        tipoPacote = pacote_recebido[0] >> 4
        if tipoPacote == self.ControlPacketTypes.CONNACK:
            # se tamanho for diferente de 4, o pacote está mal formatado
            if tamanho != 4:
                return
            # se byte 1 for diferente de 2, o pacote está mal formatado
            if pacote_recebido[1] != 2:
                return
            # código de retorno = 0 significa que a conexão foi aceita
            if pacote_recebido[3] == 0:
                self.connected_flag = True
                print("Conexão aceita")
            else:
                print("Erro na conexão, resposta: {}".format(pacote_recebido[3]))
        return
        """