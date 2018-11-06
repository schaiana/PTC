#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Sep 27 13:53:35 2018

@author: msobral
"""
from ipaddress import ip_address as IP
import struct
import fcntl
import os
import socket

class Tun:
    '''Interfaces tun: possibilita criar e destruir interfaces tun,
além de enviar e receber quadros através desse tipo de interface'''

    Defargs = {'mask': '255.255.255.255', 'mtu': 248, 'qlen': 4}
    
    ifreq = '16s24c'
    IFF_TUN = 1
    IFF_UP = 1
    IFF_RUNNING = 0x40
    PROTO_IPV4=0x0800
    PROTO_IPV6=0x866d

    TUNSETIFF = 0x400454ca
    SIOCSIFADDR = 0x8916
    SIOCSIFDSTADDR = 0x8918
    SIOCSIFNETMASK = 0x891c
    SIOCSIFMTU = 0x8922
    SIOCSIFTXQLEN = 0x8943
    SIOCGIFFLAGS = 0x8913
    SIOCSIFFLAGS = 0x8914
    
    def __init__(self, name, ip, dstip, ** args):
        '''Define uma interface tun, mas ainda não a cria. Os parâmetros de configuraçao dessa interface devem ser informados nos argumentos:
        name: nome da interface tun
        ip: endereço IPv4 desta interface
        dstip: endereço IPv4 da outra ponta do enlace
        args: "key arguments" opcionais 
          mask=máscara de rede (str)
          mtu=MTU (int)
          qlen=comprimento da fila de saída (int)
        '''
        self.name = name.encode('ascii')
        self.ip = IP(ip)
        self.dstip = IP(dstip)
        self.mask = IP(self._getarg('mask', args))
        self.mtu = self._getarg('mtu', args)
        self.qlen = self._getarg('qlen', args)
        self.fd = -1
        
    def __del__(self):
        self.stop()
        
    def _getarg(self, k, args):
        try:
            return args[k]
        except KeyError:
            return Tun.Defargs[k]
        
    def stop(self):
        'Para e remove a interface tun'
        if self.fd >= 0: os.close(self.fd)

    def start(self):
        'Cria a interface tun, e configura-a com seu endereço IP'
        if self.fd >= 0: raise ValueError('already started')
        self._alloc()
        self._setIp()
        
    def send_frame(self, dados, proto):
        '''Envia os dados para a interface tun.
           dados: buffer com os bytes a enviar (bytes ou bytearray)
           proto: número do protocolo'''
        frame = struct.pack('!HH%ds' % len(dados), 0, proto, dados)
        os.write(self.fd, frame)

    def get_frame(self):
       '''Recebe dados da tun. Retorna uma tupla (proto,dados):
           dados: buffer com os bytes recebido (tipo bytes)
           proto: número do protocolo'''
       dados = os.read(self.fd, self.mtu+4)
       flags,proto,payload = struct.unpack('!HH%ds' % (len(dados)-4), dados)
       return proto,payload

    def _alloc(self):
        ifr = bytearray(b'0'*40)
        
        self.fd = os.open('/dev/net/tun', os.O_RDWR)
        ifr = struct.pack('16sh22x', self.name, Tun.IFF_TUN)
        try:
            fcntl.ioctl(self.fd, Tun.TUNSETIFF, ifr)
        except OSError as e:
            os.close(self.fd)
            raise e
            
        if not self.name:
            name,flag = struct.unpack('16sh22x', ifr)
            self.name = name.strip(b'\x00')
            
    def _genaddr(self, ip):
        # struct sockaddr_in
        addr = struct.pack('HH4s8x', socket.AF_INET, 0, ip.packed)
        ifr = struct.pack('16s16s8x', self.name, addr)
        return ifr
        
    def _setIp(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, 0)
        fcntl.ioctl(s, Tun.SIOCSIFADDR, self._genaddr(self.ip))
        fcntl.ioctl(s, Tun.SIOCSIFDSTADDR, self._genaddr(self.dstip))
        fcntl.ioctl(s, Tun.SIOCSIFNETMASK, self._genaddr(self.mask))
        ifr = struct.pack('16sI20x', self.name, self.mtu)
        fcntl.ioctl(s, Tun.SIOCSIFMTU, ifr)
        ifr = struct.pack('16sI20x', self.name, self.qlen)
        fcntl.ioctl(s, Tun.SIOCSIFTXQLEN, ifr)
        fcntl.ioctl(s, Tun.SIOCGIFFLAGS, ifr)
        name,flag = struct.unpack('16sH22x', ifr)
        flag |= Tun.IFF_UP | Tun.IFF_RUNNING
        ifr = struct.pack('16sH22x', self.name, flag)        
        fcntl.ioctl(s, Tun.SIOCSIFFLAGS, ifr)
        
        
        
        
        
        
