# -*- coding: utf-8 -*-
#Interpreta o arquivo como utf-8 (aceita acentos)
from enum import Enum
from binascii import unhexlify
import enlayce
import enquadramento
import time

class ARQ:

	def __init__(self, enq, idSessao, timeout):
		self.Estados = Enum('Estados', 'ocioso espera') 
		self.estado = self.Estados.ocioso
		self.TipoEvento = Enum('TipoEvento','payload quadro timeout')
		self.evento = None
		self.timeout = timeout
		self.buf = bytearray()
		self.dado = bytearray()
		self.enq = enq
		self.n = 1 #controle envio
		self.m = 0 #controle recepção
		self.payload_recebido = bytearray()		
		self.read = False
		self.dado_envio = bytearray()
		self.idSessao = idSessao
		self.last_time = time.time()
		self.maxTentativas = 5
		self.nTentativas = 0

	def envia(self, dado):

		if (dado == bytearray()):
			return
		self.evento = self.TipoEvento.payload
		self.dado = dado

		self._handle(self.evento)
		#print ('ARQ Payload tratado e enviado.')
		return
					
	def recebe(self):
		tam, self.buf = self.enq.recebe()

		if (self.buf == bytearray()):
			return 0, bytearray()

		self.evento = self.TipoEvento.quadro

		self._handle(self.evento)
		return len(self.buf), self.buf

	def _handle(self, evento):
		if (self.estado == self.Estados.ocioso):
			self.estado = self._func_ocioso(evento)
			return self.estado
		elif (self.estado == self.Estados.espera):
			self.estado = self._func_espera(evento)
			return self.estado

	def _func_ocioso(self, evento):
		if (self.evento == self.TipoEvento.payload):			
			if (self.n == 1):
				self.n = 0
			else:
				self.n = 1
			#print('Enviando Dado{}'.format(self.n))
			return self._func_payload()
		elif (self.evento == self.TipoEvento.quadro):
			self._func_quadro()
			return self.estado


	def _func_espera(self, evento):
		if (evento == self.TipoEvento.payload):
			tam, self.buf = self.enq.recebe()
			if (tam == 0):
				return self.Estados.espera
			self._func_quadro()
			if (self.buf == bytearray()):
				return self.Estados.espera
			return self.Estados.ocioso
		elif(evento == self.TipoEvento.quadro):
			if (self.buf ==  bytearray()):
				return self.Estados.ocioso
			return self._func_quadro()		
		return self.Estados.espera


	def _func_payload(self):
		controle = 0b00000000
		if (self.n == 1):
			controle = controle | 0b00001000

		self.dado_envio = bytearray()
		self.dado_envio = self.dado_envio + bytes([controle]) + bytes([self.idSessao]) + self.dado
		self.enq.envia(self.dado_envio)	
		self.last_time = time.time()
		self.nTentativas = self.nTentativas +1		
		return self.Estados.espera

	def _func_quadro(self):
		if (self.buf[1:2] != bytes([self.idSessao])):
			print('Recebeu pacote com ID de sessão diferente da sessão ativa')
			self.buf = bytearray()
			return self.estado
		controle = self.buf[0]
		if (((controle & 0b10000000) >> 7) == 1): #quadro de ack
			if (((controle & 0b00001000) >> 3) == self.n):
				self.last_time = time.time()
				self.nTentativas = 0
				self.buf = bytearray()
				return self.Estados.ocioso
			else:
				self._func_payload()
				return self.Estados.espera
		else: #quadro de dados
			return self._func_remove_frame()
		

	def _func_remove_frame(self):
		controle = self.buf[0]
		if (((controle & 0b10000000) >> 7) == 0): #se for data (0 & 1 = 0)
			if (((controle & 0b00001000) >> 3) == self.m): #M
			 	#envia o ackM e manda payload para a app
				self.payload_recebido = self.buf[3:]
				#print ('Recebeu payload: {}'.format(self.payload_recebido.decode('utf-8')))
				self._func_ack(self.m)
				return self.estado 
			else: #!M (m barrado) - reenvia ack de pacote já recebido
				self._func_ack(self.m ^ 1)
				return self.estado
	
	def _func_ack(self, mEnvia):
		ack = bytearray()
		controle = 0b10000000
		if (mEnvia == 1):
			controle = controle | 0b00001000
		#print ('Enviando ACK{}'.format(mEnvia))
		
		ack = ack + bytes([controle]) + bytes([self.idSessao])

		self.enq.envia(ack)
	
	def func_timeout(self):
		if(self.estado == self.Estados.espera):
			time_dif = time.time()-self.last_time
			if(time_dif>self.timeout):
				if(self.nTentativas>self.maxTentativas): # se excedeu o número de tentantivas, desiste de enviar o payload
					self.last_time = time.time()
					self.nTentativas = 0
					self.buf = bytearray()
					self.estado = self.Estados.ocioso
				else:
					self._func_payload()