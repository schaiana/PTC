# -*- coding: utf-8 -*-
#Interpreta o arquivo como utf-8 (aceita acentos)
import SchaiLay
import sys

if(len(sys.argv) < 4):
	print('É necessário informar o ip e porta do servidor e o nome do arquivo')
	print('Ex.: client.py 127.0.0.1 69 teste.txt')
	exit()

serverIp = sys.argv[1]
serverPort = int(sys.argv[2])
fileName = sys.argv[3] 

SchaiLay.setTimeout(5)
SchaiLay.nRetries(2)
SchaiLay.sendFile(serverIp, serverPort, fileName)