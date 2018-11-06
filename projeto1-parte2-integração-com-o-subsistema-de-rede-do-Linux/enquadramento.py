# -*- coding: utf-8 -*-
#Interpreta o arquivo como utf-8 (aceita acentos)
from enum import Enum
from binascii import unhexlify
import time

class Enquadramento:


	def __init__(self, serial, timeout, bytes_min = 0, bytes_max = 256):
		self.serial = serial
		self.timeout = timeout
		self.min_bytes = bytes_min
		self.max_bytes = bytes_max
		self.buf = bytearray()
		self.Estados = Enum('Estados', 'ocioso rx recepcao esc')
		self.estado = self.Estados.ocioso
		self.buf_poller = bytearray()
		self.serial.reset_input_buffer()
		self.serial.reset_output_buffer()
		self.last_time = time.time()
		

	def envia(self, dado):
		import crc
		dado_transformado = bytearray()	
		fcs = crc.CRC16(dado)
		dado_com_crc = fcs.gen_crc()
		

		for i in range(0,len(dado_com_crc)):					
			if ((dado_com_crc[i] == 0x7E) or (dado_com_crc[i] == 0x7D)):
				dado_transformado = dado_transformado + b'\x7D' + bytes([self._xor20(dado_com_crc[i])])
				#print('teste')
			else:
				dado_transformado = dado_transformado + bytes([dado_com_crc[i]]) #dado entre colchetes para transformar para bytes
		buf = bytearray()
		buf = buf + b'\x7E' + dado_transformado + b'\x7E'		

		self.serial.write(buf)
	
	#recebe byte do poller e manda pro handle
	def trata_byte(self, byte_recebido):
		import crc
		#print('Trata byte: {}'.format(byte_recebido))
		if (self._handle(byte_recebido) == True): # terminou de receber
			dado_recebido = self.buf #[0:-4]
			dado_sem_crc = self.buf[0:-2]
			fcs = crc.CRC16('')
			fcs.clear()
			fcs.update(dado_recebido)
			crc_valido = fcs.check_crc()		
			#print('Trata byte - quadro completo: {}'.format(dado_sem_crc))
			if(crc_valido == True):				
				#return len(dado_sem_crc), dado_sem_crc
				self.buf_poller = dado_sem_crc
				return True
			else:
				#print('Pacote corrompido e descartado.')
				dado_recebido = bytearray()	
				#return 0, dado_recebido	
				self.buf_poller = dado_recebido
				return False

	def recebe(self):
		buf_temp = self.buf_poller
		self.buf_poller = bytearray()
		return len(buf_temp), buf_temp			
						
				
	# aqui se implementa a máquina de estados de recepção
	# retorna true se reconheceu um quadro completo
	def _handle(self, byte_recebido):
		#print('Tratando estado {}'.format(self.estado))
		if (self.estado == self.Estados.ocioso):
			self.estado = self._func_ocioso(byte_recebido)
			#print(self.estado)
			return False
		elif (self.estado == self.Estados.rx):
			self.estado = self._func_rx(byte_recebido)
			#print(self.estado)
			return False
		elif (self.estado == self.Estados.esc):
			self.estado = self._func_esc(byte_recebido)
			#print(self.estado)
			return False
		else:
			self.estado = self._func_recepcao(byte_recebido)
			#print(self.estado)
			if (self.estado == self.Estados.ocioso): #Transição de recepcao para ocioso, recebeu quadro completo
				return True
			return False
				

	def _func_ocioso(self, byte_recebido):

		if (byte_recebido != b'\x7E'): #Se o byte recebido não for o 7E (01111110), fica no estado ocioso
			return self.Estados.ocioso
		elif (byte_recebido == b'\x7E'):
			self.buf = bytearray()
			return self.Estados.rx

	def _func_rx(self, byte_recebido):
		self.last_time = time.time()
		if (byte_recebido == b'\x7E'):
			return self.Estados.rx
		elif (byte_recebido == b'\x7D'): #7D
			return self.Estados.esc
		elif (byte_recebido != b'\x7E' and byte_recebido != b'\x7D'):
			self.buf = self.buf + byte_recebido
			return self.Estados.recepcao


	def _func_recepcao(self, byte_recebido):
		self.last_time = time.time()
		if (byte_recebido != b'\x7E' and byte_recebido != b'\x7D'):
			self.buf = self.buf + byte_recebido
			if (len(self.buf) > self.max_bytes):
				self.buf = bytearray()
				return self.Estados.ocioso
			return self.Estados.recepcao
		elif (byte_recebido == b'\x7D'):
			return self.Estados.esc
		elif (byte_recebido == b'\x7E'):
			return self.Estados.ocioso
		

	def _func_esc(self, byte_recebido):
		self.last_time = time.time()
		if (byte_recebido == b'\x7E' or byte_recebido == b'\x7D'):
			self.buf = bytearray()
			return self.Estados.ocioso
		else:
			byte_transformado = self._xor20(byte_recebido[0])
			self.buf = self.buf + bytes([byte_transformado])
			return self.Estados.recepcao
			
	def _xor20(self, byte_recebido):
		byte_transformado = byte_recebido ^ 0x20
		return byte_transformado

	def func_timeout(self):
		if(self.estado in [self.Estados.rx, self.Estados.recepcao, self.Estados.esc]):
			timedif = time.time()-self.last_time
			if(timedif>self.timeout):
				self.buf = bytearray()
				self.estado = self.Estados.ocioso

