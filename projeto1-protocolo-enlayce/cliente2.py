# -*- coding: utf-8 -*-
#Interpreta o arquivo como utf-8 (aceita acentos)
import enlayce
import sys


if(len(sys.argv) < 2):
	print('É necessário informar a porta serial, a ID da sessão e o tempo de timeout')
	print('Ex.: cliente2.py /dev/pts/37 123 5')
	exit()

p_serial = sys.argv[1]
idSessao = int(sys.argv[2])
timeout = float(sys.argv[3])

enl = enlayce.Enlayce(p_serial, idSessao, timeout)

tam_buf, buf = enl.recebe()
print('Cliente 2 recebeu a mensagem: {}'.format(buf.decode()))


dado = input('Digite um dado para transmissão:\n').encode('utf-8')

dado = bytearray(dado)

#print('Cliente 2 envia o payload: {}'.format(dado.decode()))
enl.envia(dado)
#print('Payload enviado')
#print('Cliente 2: Finalizando...')
enl.encerra()










