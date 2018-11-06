# -*- coding: utf-8 -*-
#Interpreta o arquivo como utf-8 (aceita acentos)
#import crcmod.predefined
from enum import Enum
import ARQ
import enlayce
import time

class Sessao:
	Estados = Enum('Estados', 'disc hand1 hand2 con check half1 half2')
	def __init__(self, arq, timeout):
		self.Estados = Sessao.Estados
		self.arq = arq		
		self.timeout = timeout
		self.timeout_grande = 3*timeout
		self.estado = self.Estados.disc
		self.dado = bytearray()
		self.dado_envio = bytearray()
		self.dado_recebido = bytearray()
		self.buf = bytearray()  
		self.start = False
		#self.stop = False
		self.CR = b'\x00'
		self.CC = b'\x01'
		#self.KR = b'\x02'
		#self.KC = b'\x03'
		self.DR = b'\x04'
		self.DC = b'\x05'
		self.proto = b'\xff'
		self.last_time = time.time()


	def conectado(self):
		if (self.estado == self.Estados.con):
			return True
		else:
			return False

	def espera_conexao(self):
		while (self.conectado() != True):
			self._handle()

	def inicia(self):		
		if (not(self.estado in [self.Estados.disc, self.Estados.hand1, self.Estados.hand2])):
			return
		if(self.start==True):
			return
		self.estado = self.Estados.disc
		self.start = True				
		self._handle()
		if (self.estado == self.Estados.con):
			return

	def envia(self, dado):
		if(self.conectado()==False):
			return
		self.dado = bytearray()
		self.dado = self.dado + b'\x00' + dado

		while (True):
			if (self._handle() == False):
				#print ('Payload tratado e enviado.')
				return
			else:
				return self.encerra()
				

	def recebe(self):
		#print('Sessão recebe')
		tam, self.dado_recebido = self.arq.recebe()
		if (self._handle() == False):
			#if (self.dado_recebido == bytearray()):
			#	continue
			#print('Sessão recebeu: {}'.format(self.dado_recebido))
			temp = self.dado_recebido
			self.dado_recebido = bytearray()
			return len(temp), temp
		else:
			#print('Sessão encerrou!')	
			return bytearray()

	def encerra(self):
		print ('Iniciando negociação de desconexão...')
		self._func_DR()
		self.estado = self.Estados.half1
		while (True):
			if (self._handle() == False):
				if len(self.buf) > 0:
					return self.buf
			else:
				self.estado = self.Estados.disc			
				return bytearray()


	def _handle(self):
		#print(self.estado)
		if (self.estado == self.Estados.disc):
			self.estado = self._func_disc()
			return False
		elif (self.estado == self.Estados.hand1):
			self.estado = self._func_hand1()
			return False
		elif (self.estado == self.Estados.hand2):
			self.estado = self._func_hand2()
			return False
		elif (self.estado == self.Estados.con):
			self.estado = self._func_con()
			return False
		elif (self.estado == self.Estados.half1):
			self.estado = self._func_half1()
			if (self.estado == self.Estados.disc):
				return True
			return False
		else: #half2
			self.estado = self._func_half2()
			if (self.estado == self.Estados.disc):
				return True
			return False

	def _func_disc(self):
		#print('Sessao _func_disc')
		if (self.start == True):
			#envia o CR montado para ARQ
			print ('Iniciando negociação de conexão...')
			self._func_CR()
			self.last_time = time.time()
			return self.Estados.hand1
		else:
			#tam, self.buf = self.arq.recebe()
			self.buf = self.dado_recebido
			#print(self.buf)
			tam = len(self.dado_recebido)
			if (tam == 0):
				return self.Estados.disc
			#envia o CC montado para ARQ
			if (self.buf[2:3] == self.proto[0:1] and self.buf[3:4] == self.CR[0:1]):
				print ('Recebeu CR! Tratando pedido negociação de conexão...')
				self.dado_envio = bytearray()
				self.dado_envio =  self.dado_envio + self.proto + self.CC	
				print ('Enviando CC.')
				self.arq.envia(self.dado_envio)			
				return self.Estados.hand2
			return self.Estados.disc

	def _func_CR(self):
		self.dado_envio = bytearray()
		self.dado_envio = self.dado_envio + self.proto + self.CR
		print ('Enviando CR.')
		self.arq.envia(self.dado_envio)	
		self.last_time = time.time()
		print('CR enviado')
		self.dado_envio = bytearray()

	def _func_hand1 (self):	
		#tam, self.buf = self.arq.recebe()
		self.buf = self.dado_recebido
		tam = len(self.buf)
		if (tam == 0):
			self._func_CR()
			return self.Estados.hand1

		if (self.buf[3:4] == self.CC[0:1]):  #Recebeu CC. Envia bloco com dado vazio (proto zerado)
				print ('Recebeu CC.')
				self.dado_envio =  self.dado_envio + b'\x00' + b'\x00'
				print ('Enviando CC com dado zerado.')	
				print ('Conexão estabelecida.')	
				self.arq.envia(self.dado_envio)
				return self.Estados.con
		return self.Estados.hand1	
				
	def _func_hand2(self):
		#tam, self.buf = self.arq.recebe()
		self.buf = self.dado_recebido
		tam = len(self.buf)		
		if (tam == 0):
			return self.Estados.hand2
		#print('*** {}'.format(self.buf))
		if (self.buf[2:3] == self.proto[0:1] and self.buf[3:4] == b'\x00'):
			print ('Conexão estabelecida.')
			return self.Estados.con
			
		return self.Estados.hand2

			
	def _func_con (self):
		if (self.dado != bytearray()):
			self.arq.envia(self.dado)
			self.dado = bytearray()
			return self.Estados.con
		#tam, self.buf = self.arq.recebe()
		self.buf = self.dado_recebido
		tam = len(self.buf)
		if (tam > 0):
			if (self.buf[2:3] == self.proto[0:1] and self.buf[3:4] == self.DR[0:1]): ## Recebeu pedido de encerramento do clienteRecebe
				print ('Recebeu pedido de DR')			
				self._func_DR()
				return self.Estados.half2
			else:
				self.dado_recebido = self.buf[3:]
				return self.Estados.con
		return self.Estados.con

	def _func_DR(self):
		self.dado_envio = bytearray()
		self.dado_envio = self.dado_envio + self.proto + self.DR
		print ('Enviando DR.')
		self.arq.envia(self.dado_envio)	

	def _func_half1 (self):
		#tam, self.buf = self.arq.recebe()
		self.buf = self.dado_recebido
		tam = len(self.buf)
		if (tam == 0):
			self._func_DR()
			return self.Estados.half1

		if (self.buf[3:4] == self.DR[0:1]):
			print ('Recebeu confirmação de DR.')
			self.dado_envio = bytearray()
			self.dado_envio = self.dado_envio + self.proto + self.DC
			print ('Enviando DC.')
			#print(self.dado_envio)
			self.arq.envia(self.dado_envio)
			print('Sessão encerrou!')
			return self.Estados.disc
		return self.Estados.half1

	def _func_half2 (self): 
		#tam, self.buf = self.arq.recebe()
		self.buf = self.dado_recebido
		tam = len(self.buf)
		if (tam == 0):	
			print('DC não recebido. Encerrando...')
			return self.Estados.disc		
		if(self.buf[3:4] == self.DR[0:1]):
			self._func_DR()
			return self.Estados.half2
		if(self.buf[3:4] == self.DC[0:1]):
			print('Sessão encerrou!')
			return self.Estados.disc

	def func_timeout(self):
		if(self.estado == self.Estados.hand1):
			time_dif = time.time() - self.last_time
			if(time_dif>self.timeout):
				self._func_CR()
		if(self.estado == self.Estados.hand2):
			time_dif = time.time() - self.last_time
			if(time_dif>self.timeout):
				self.estado = self.Estados.disc
				self.start = False
				self.last_time = time.time()

