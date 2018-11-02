# -*- coding: utf-8 -*-
#Interpreta o arquivo como utf-8 (aceita acentos)
import ARQ
import serial
import enquadramento
import sessao

class Enlayce:


	def __init__(self, p_serial, idSessao, timeout, bytes_min = 0, bytes_max = 256):

		self.min_bytes = bytes_min
		self.max_bytes = bytes_max
		self.timeout = timeout
		self.ser = serial.Serial(p_serial, 9600, timeout = self.timeout) #timeout = timeout do método read da Serial
		self.enq = enquadramento.Enquadramento(self.ser, self.timeout)
		self.arq = ARQ.ARQ(self.enq, idSessao, self.timeout)
		self.sessao = sessao.Sessao(self.arq, self.timeout)

	def envia(self, dado):
		if (self.sessao.conectado() == False):
			self.sessao.inicia()		
		return self.sessao.envia(dado) #retorna para a aplicação quando chegar o ack da outra aplicação, desbloqueando a mesma para um novo envio


	def recebe(self):

		if (self.sessao.conectado() == False):
			self.sessao.espera_conexao()
		return self.sessao.recebe() #retorna o payload para a aplicação		

	def encerra(self):
		return self.sessao.encerra()
						

