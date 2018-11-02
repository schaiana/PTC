# -*- coding: utf-8 -*-
#Interpreta o arquivo como utf-8 (aceita acentos)
import socket
import sys
import os.path

# variáveis em comum entre cliente e servidor
_arq = None
_udp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
_tempoTimeout = 10 # tempo de timeout em segundos
_retries = 5 # número de vezes que o cliente/servidor irá tentar enviar/receber o arquivo em caso de timeout

#variáveis do cliente
_cl_numPacketAtual = 0 # número do último pacote enviado (cliente)
_cl_quantPacket = 0 # quantidade todal de pacotes a ser enviado (cliente)
_cl_nameArqSend = '' #nome do arquivo a ser enviado
_cl_dest = None #estrutura (host, port) do servidor

#variáveis do servidor
_sv_numLast = 0 # número do último pacote recebido
_sv_cliente_atual = None # socket udp do cliente que está enviando o arquivo

######################
### Parte em comum ###
######################

# tempo de timeout em segundos
def setTimeout(nSeconds):
	global _tempoTimeout
	_tempoTimeout = nSeconds

# número de vezes que o cliente/servidor irá tentar enviar/receber o arquivo em caso de timeout
def nRetries(nRetries):
	global _retries
	_retries = nRetries 

########################
### Parte do cliente ###
########################

def sendFile(host, port, arq_name):
	global _udp, _cl_dest, _cl_quantPacket, _cl_numPacketAtual, _arq, _cl_nameArqSend

	_cl_nameArqSend = arq_name
	_cl_dest = (host, port)

	_arq = _cl_leArq(_cl_nameArqSend)
	
	#número do bloco a ser enviado
	num_to_send = 0

	#calculo da quantidade de pacotes
	_cl_quantPacket = _cl_tamanhoArq(_arq) #quantidade de pacotes
	nTimeout = 0
	while _cl_numPacketAtual <= _cl_quantPacket:
		try:
			packet = _cl_montaPacket(num_to_send) #monta pacote
			_cl_enviaPacket(packet) #envia pacote
			_udp.settimeout(_tempoTimeout)
			msg, server = _udp.recvfrom(1024) #recebe resposta
			_udp.settimeout(None)
			num_to_send = _cl_trataResp(msg) #trata resposta
			nTimeout = 0 #recebi a resposta, reseto o número de timeout
		except socket.timeout:
			if nTimeout < _retries:
				_cl_enviaPacket(packet)
				nTimeout = nTimeout + 1
			elif nTimeout == _retries:
				print('Não foi possível enviar o arquivo. (timeout)')
				_udp.close()
				_arq.close() #fecha o arquivo
				exit()

def _cl_nomeArq(arq): #converte nome do arquivo de strig para binário
	return os.path.basename(arq).encode('utf-8') #converter de string com codificação utf-8 apenas o nome do arquivo

def _cl_tamanhoArq(arq):
	arq.seek(0,2)
	tamanho_bytes = arq.tell()
	n_blocos_int = int(tamanho_bytes / 512)
	n_blocos_float = tamanho_bytes / 512
	n_blocos = n_blocos_int
	
	if(n_blocos_float-n_blocos)!=0:
		n_blocos = n_blocos + 1
		
	# se o arquivo estiver vazio colocamos o n_blocos = 1 para mandar pelomenos um pacote de dados que indica o fim do arquivo
	if(n_blocos==0):
		n_blocos = 1
	
	return n_blocos#os.path.getsize (arq)/512

def _cl_montaPacket(numPacket):
	global _cl_quantPacket, _arq
	packet = bytearray()
	print('Gerando pacote {}'.format(numPacket))
	if numPacket == 0: #Primeiro pacote: flag 0 + opcode 2 (solicitação de escrita) + nome do arquivo
		packet = packet + b'\x00' #flag 0 em todos os pacotes N-1
		packet = packet + b'\x02' #solitação de escrita
		packet = packet + _cl_nomeArq(_cl_nameArqSend) #adiciona nome do arquivo no pacote
		packet = packet + b'\x00' #fim do nome do arquivo		
		packet = packet + _cl_nomeArq('Octet')
		
	elif numPacket != 0 and _cl_numPacketAtual != _cl_quantPacket: #Segundo pacote até N-1 pacote: flag 0 + opcode 3 (dados) + dados
		packet = packet + b'\x00' #flag 0 em todos os pacotes N-1
		packet = packet + b'\x03' #envio de dados
		
		numPacket_0 = numPacket >> 8 #11110100. Faz um deslocamento para a direita para extrair os 8 bits do início
		numPacket_1 = numPacket & 0b11111111 #10110011 #número em binário: 0b e depois o número. Faz um AND para extrair os 8 bits do fim
		
		packet = packet + bytes([numPacket_0]) #primeiro byte do número do pacote.
		packet = packet + bytes([numPacket_1]) #segundo byte do número do pacote. Ex: packet01
		
		_arq.seek(512*(numPacket-1))
		#packet = packet + _cl_dest.write(_arq.read(512))
		packet = packet + _arq.read(512)
		
	elif numPacket == _cl_quantPacket:
		packet = packet + b'\x01' #flag 1 no pacote N
		packet = packet + b'\x03' #envio de dados
		
		numPacket_0 = numPacket >> 8 #11110100. Faz um deslocamento para a direita para extrair os 8 bits do início
		numPacket_1 = numPacket & 0b11111111 #10110011 #número em binário: 0b e depois o número. Faz um AND para extrair os 8 bits do fim
		
		packet = packet + bytes([numPacket_0]) #primeiro byte do número do pacote.
		packet = packet + bytes([numPacket_1]) #segundo byte do número do pacote. Ex: packet01
		
		_arq.seek(512*(numPacket-1))
		#packet = packet + _cl_dest.write(_arq.read(512))
		packet = packet + _arq.read(512)

	return packet

def _cl_leArq(arq):
	try:
   		arquivo = open(arq,"rb")
   		#arq_cl_destino = open("teste.txt","wb")
	except:
		print("Erro ao abrir os arquivos.")

	return arquivo#arq_cl_destino

def _cl_enviaPacket(packet_enviar, nTimeout = 0):
	global _cl_dest
		
	try:
		_udp.settimeout(_tempoTimeout)
		_udp.sendto(packet_enviar, _cl_dest)	
		print('Enviou o pacote: {}'.format(packet_enviar))
		_udp.settimeout(None)
	except socket.timeout:
		if nTimeout < _retries:
			nTimeout = nTimeout + 1
			_cl_enviaPacket(packet_enviar, nTimeout)
		elif nTimeout == _retries:
			print('Não foi possível enviar o arquivo. (timeout)')
			_udp.close()
			_arq.close() #fecha o arquivo
			exit()

def _cl_trataResp(msg):
	#se erro
	if(msg[1]==5):
		_cl_trataErro(msg)
		
	global _cl_numPacketAtual
	
	nBlock = (msg[2] << 8) + msg[3] #número do bloco com 16 bytes. Fiz o shiftleft pra somar zero com o packet[3]
	print('Recebeu o ACK número {}'.format(nBlock))
		
	if (nBlock < _cl_numPacketAtual): #se o número do ack for menor que o número que eu espero, ou seja, o servidor não recebeu o packetN, envio novamente o packetN
		num_to_send = _cl_numPacketAtual
			
	elif (nBlock == _cl_numPacketAtual): #se o número do pacote for igual ao número que eu espero:
		_cl_numPacketAtual = _cl_numPacketAtual + 1
		num_to_send = _cl_numPacketAtual
		
	return num_to_send

	#número do pacote esperado é o número do último pacote recebido + 1
	#se ack retornar _cl_numPacketAtual + 1
	#se error retornar _cl_numPacketAtual + 1

def _cl_trataErro(packet):
	posicao_zero = packet.find(b'\x00', 4) #procura pelo zero que finaliza a mensagem de erro. 4 é a posição onde começa a mensagem
	msg_bin = packet[4:posicao_zero]
	msg = msg_bin.decode('utf-8')
	print(msg)
	exit()
	
	
	
#########################
### Parte do servidor ###
#########################

def startServer(PORT=69):
	global _udp, _sv_cliente_atual, nTimeout, _arq
	HOST = ''              # Endereco IP do Servidor. 
	#PORT = 69            # Porta que o Servidor esta
	#_udp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
	orig = (HOST, PORT)

	try:	
		_udp.bind(orig) #servidor escuta na interface e porta definidas acima
		nTimeout = 0
	
		while True: #espera pacote
			try:
				_udp.settimeout(_tempoTimeout)
				msg, cliente = _udp.recvfrom(1024) #msg: dados do pacote (bytes); cliente: ip do cliente que mandou aquele pacote #tamanho máximo é 1024
				print('Recebeu pacote {}'.format(msg))
				if (cliente != _sv_cliente_atual and _sv_cliente_atual != None): #se o cliente que solicitou a escrita for diferente do cliente que já estava escrevendo
					_sv_sendERR(cliente, 'Servidor ocupado! Tente novamente mais tarde.') #manda msg de erro para o cliente novo dizendo que o servidor está ocupado
					continue #volta pro início do while para esperar pacotes novos
			
				_sv_cliente_atual = cliente #armazena o cliente para caso dê timeout
				_udp.settimeout(None)
				#print (cliente, msg)
				_sv_trataPacote(msg, cliente)
				nTimeout = 0 #recebi a mensagem, reseto o número de timeout
			except socket.timeout:
				if (_sv_cliente_atual != None):
					_sv_sendACK(_sv_cliente_atual, _sv_numLast) #reenvia o último ACKN
					nTimeout = nTimeout + 1
					if (nTimeout == _retries): #quando chega a 5 tentativas de reenvio
						if (_arq != None): #verifica se o _arquivo estava aberto
							_arq.close() #fecha o arquivo
							_arq = None
						_sv_cliente_atual = None #reseta o cliente que estava transmitindo
			except (KeyboardInterrupt, SystemExit):
				if _udp!=None:
					_udp.close()
				if (_arq != None): #verifica se o arquivo estava aberto
					_arq.close() #fecha o arquivo
					_arq = None
				exit()
			except:
				_sv_cliente_atual = None
				if (_arq != None): #verifica se o arquivo estava aberto
					_arq.close() #fecha o arquivo
					_arq = None
	finally:
		if _udp!=None:
			_udp.close()
 
def _sv_trataPacote(packet, cliente):
	#print(packet[0]) #primeiro byte do opcode é zerado
	
	if (packet[1] == 2): #opcode: escrita. b'\x02'. O python transforma o packet[1] em 2 em decimal, por isso a comparação fica assim
		_sv_opWRQ(packet, cliente)
	elif (packet[1] == 3): #opcode: dados. b'\x03
		_sv_opData(packet, cliente)
	else:
		print('Pacote desconhecido') #não é pacote de escrita nem de dados
		print(packet[1]) #segundo byte do opcode é a operação que será feita, o print mostra em decimal

def _sv_opWRQ(packet, cliente):	
	global _sv_numLast, _arq, _udp
	
	print('Recebeu requisição para escrever um arquivo')
	
	modo = _sv_extraiModo(packet)
	if(modo.upper() != 'OCTET'):
		print(modo)
		_sv_cliente_atual = None
		_sv_sendERR(cliente, 'O modo {} não é suportado, tente OCTET'.format(modo))
		return
		
	
	nome_arq = _sv_extraiNomeArquivo(packet) #pega nome do arquivo
	print('Nome do arquivo: {}'.format(nome_arq))
	try:
		_arq = open(nome_arq, 'wb') 
	except:
		print('Erro ao abrir o arquivo')
	_sv_numLast = 0
	_sv_sendACK(cliente, _sv_numLast) #0 porque é sempre o primeiro ACK - solicitação de escrita recebida
	
def _sv_sendACK(cliente, nAck):
	global _udp
	ack_packet = bytearray(4)
	ack_packet[0] = 0
	ack_packet[1] = 4
	#1111010010110011
	nAck_0 = nAck >> 8 #11110100. Faz um deslocamento para a direita para extrair os 8 bits do início
	nAck_1 = nAck & 0b11111111 #10110011 #número em binário: 0b e depois o número. Faz um AND para extrair os 8 bits do fim
	ack_packet[2] = nAck_0 #primeiro byte do número do ack.
	ack_packet[3] = nAck_1 #segundo byte do número do ack. ex: ACK01
	_udp.sendto(ack_packet, cliente)
	

def _sv_opData(packet, cliente):	
	global _sv_numLast, _arq, _sv_cliente_atual

	nBlock = (packet[2] << 8) + packet[3] #número do bloco com 16 bytes. Fiz o shiftleft pra somar zero com o packet[3]
	print('Recebeu pacote de dados número {}'.format(nBlock))
	num_esperado = _sv_numLast + 1; #número do pacote esperado é o número do último pacote recebido + 1
	
	if (nBlock < num_esperado): #se o número do pacote for menor que o número que eu espero, ou seja, o cliente não recebeu o ACKN, envio novamente o ACKN
		_sv_sendACK(cliente, _sv_numLast)
	elif (nBlock == num_esperado): #se o número do pacote for igual ao número que eu espero:
		_arq.write(packet[4:]) #escrevo no arquivo
		_sv_numLast = _sv_numLast + 1 #incremento o número atual do bloco de dados
				
		#implementação seguindo a RFC1350
		#tam_packet = len(packet) #tamanho total do pacote
		#tam_data = tam_packet - 4 #tamanho total do pacote menos 2 bytes de opcode e 2 bytes do número do bloco
		#if (tam_data < 512): #se o tamanho do data for menor do que 512, é o último pacote
		#	_arq.close()
		#	_arq = None
		#	print('Encerrou o arquivo')
		#	_sv_cliente_atual = None
		
		#implementação sugerida em sala de aula (flag)
		#decidimos pôr a flag num byte que era sempre zerado: primeiro byte do opcode. Se for 1, é o último pacote do arquivo
		if (packet[0] == 1):
			_arq.close()
			_arq = None
			print('Encerrou o arquivo')
			_sv_cliente_atual = None
			
		_sv_sendACK(cliente, _sv_numLast) #envio o ACKN	

def _sv_extraiModo(packet):
	posicao_zero = packet.find(b'\x00', 2) #procura pelo zero que finaliza o nome do arquivo. 2 é a posição onde começa o nome do arquivo
	modo_bytes = packet[posicao_zero+1:]
	modo = modo_bytes.decode('utf-8') #converter para string com codificação utf-8, que é mais genérico
	return modo
	
def _sv_extraiNomeArquivo(packet):
	posicao_zero = packet.find(b'\x00', 2) #procura pelo zero que finaliza o nome do arquivo. 2 é a posição onde começa o nome do arquivo
	nome_bytes = packet[2:posicao_zero]
	nome_arq = nome_bytes.decode('utf-8') #converter para string com codificação utf-8, que é mais genérico
	#print(nome_arq)
	return nome_arq
		
def _sv_sendERR(cliente, msg_err):
	#msg_err = 'Servidor ocupado! Tente novamente mais tarde.'
	err_packet = bytearray()
	err_packet = err_packet + b'\x00' #opcode erro
	err_packet = err_packet + b'\x05' #opcode erro
	err_packet = err_packet + b'\x00' #tipo erro
	err_packet = err_packet + b'\x00' #tipo erro
	err_packet = err_packet + msg_err.encode('utf-8') #msg erro
	err_packet = err_packet + b'\x00' #fim
	_udp.sendto(err_packet, cliente) #envia erro pro cliente
	

#2 bytes  2 bytes        string    1 byte
#----------------------------------------
#| 05    |  ErrorCode |   ErrMsg   |   0  |

	
#testes	
#Exemplo de packet: b'\x00\x0207572132.pdf\x00octet\x00'
#\x00 é o zero em hexadecimal, como ele não tem uma representação em caractere, usa-se a notação em hexadecimal, que é \x00 ou \x02 para o 2.

#checksum de MD5
#C:\Users\schai\Documents\Downloads\PTC_Atividade1>CertUtil -hashfile 07572132.pdf MD5
#MD5 hash de 07572132.pdf:
#1b9cb0e514555adc2bb77bb5b5d7fce4
#CertUtil: -hashfile : comando concluído com êxito.
