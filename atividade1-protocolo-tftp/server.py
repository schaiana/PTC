# -*- coding: utf-8 -*-
#Interpreta o arquivo como utf-8 (aceita acentos)
import SchaiLay
import sys

if(len(sys.argv) < 2):
	print('É necessário informar a porta em que o servidor irá operar')
	print('Ex.: server.py 69')
	exit()

port = int(sys.argv[1])

SchaiLay.setTimeout(5)
SchaiLay.nRetries(2)
SchaiLay.startServer(port)
