# -*- coding: utf-8 -*-
#Interpreta o arquivo como utf-8 (aceita acentos)
import ARQ
import serial
import enquadramento
import sessao
from tun import Tun
import os
import time
import poller
import sys


class Enlayce:


	def __init__(self, p_serial, idSessao, timeout, ip1, ip2, bytes_min = 0, bytes_max = 256):

		self.min_bytes = bytes_min
		self.max_bytes = bytes_max
		self.timeout = timeout
		self.ser = serial.Serial(p_serial, 9600, timeout = self.timeout) #timeout = timeout do método read da Serial
		self.enq = enquadramento.Enquadramento(self.ser, 0.05)
		self.arq = ARQ.ARQ(self.enq, idSessao, self.timeout)
		self.sessao = sessao.Sessao(self.arq, self.timeout)
		self.tun = Tun("tun1",ip1,ip2,mask="255.255.255.252",mtu=1500,qlen=4)
		self.tun.start()
		self.cb_tun = CallbackTun(self.tun, self) #self = próprio enlayce
		self.sched = poller.Poller()
		self.sched.adiciona(self.cb_tun)
		self.cb_serial = CallbackStdin(self)
		self.timer = CallbackTimer(0.01, self)
		self.sched.adiciona(self.cb_serial)
		self.sched.adiciona(self.timer)
		self.sched.despache()


	def envia(self, dado):
		#print('Enlayce envia!')
		if (self.sessao.conectado() == False):
			self.sessao.inicia()
			return	
		print('Enviando')
		print(dado)	
		return self.sessao.envia(dado) #retorna para a aplicação quando chegar o ack da outra aplicação, desbloqueando a mesma para um novo envio


	def recebe(self):

		#if (self.sessao.conectado() == False):
		#	self.sessao.espera_conexao()
		tam, buf = self.sessao.recebe()
		if((type(buf)==bytearray) and buf!=bytearray()):
			print('Recebeu')
			print(buf)
			self.tun.send_frame(buf, Tun.PROTO_IPV4)
		
	def encerra(self):
		return self.sessao.encerra()

	def func_timeout(self):
		self.enq.func_timeout()
		self.arq.func_timeout()
		self.sessao.func_timeout()

class CallbackTun(poller.Callback):
    
	def __init__(self, tun, enl):
		poller.Callback.__init__(self, tun.fd, 1000)
		self._tun = tun
		self.enl = enl

	def handle(self):
		proto, payload = self._tun.get_frame()
		#print('Lido tun:', payload)
		self.enl.envia(payload)
        
	def handle_timeout(self):
		print('Timeout !')
   

class CallbackStdin(poller.Callback):
	def __init__(self, enl):
		poller.Callback.__init__(self, enl.ser, 1000)
		self.p_serial = enl.ser
		self.enl = enl


	def handle(self):
		l = self.p_serial.read()
		#print('Lido serial:', l)
		if (self.enl.enq.trata_byte(l) == True):
			#print('Recebe STDIN')
			self.enl.recebe()
        
	def handle_timeout(self):
		print('Timeout !')

class CallbackTimer(poller.Callback):

	t0 = time.time()
    
	def __init__(self, tout, enl):
		poller.Callback.__init__(self, None, tout)
		self.enl = enl
        
	def handle_timeout(self):
		self.enl.func_timeout()
		#if(self.enl.sessao.estado == sessao.Sessao.Estados.disc):
		#if(self.enl.sessao.conectado()==False):
		#	print('Conectando...')
		#	self.enl.sessao.inicia()
		#print('Timer: t=', time.time()-CallbackTimer.t0)
        



						


