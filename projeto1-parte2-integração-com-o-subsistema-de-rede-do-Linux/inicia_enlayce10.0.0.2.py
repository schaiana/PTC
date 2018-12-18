# -*- coding: utf-8 -*-
#Interpreta o arquivo como utf-8 (aceita acentos)
import enlayce
import sys


if(len(sys.argv) < 2):
	print('É necessário informar a porta serial, a ID da sessão e o tempo de timeout')
	print('Ex.: inicia_enlayce10.0.0.2.py /dev/pts/38 123 5')
	exit()

p_serial = sys.argv[1]
idSessao = int(sys.argv[2])
timeout = float(sys.argv[3])

enl = enlayce.Enlayce(p_serial, idSessao, timeout, "10.0.0.2", "10.0.0.1")
