#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
sys.path.append('../')
from utils import log
from coder import comm_encode,res_decode
from time import sleep
import socket
import re


class Client():
	def __init__(self, client_address, client_conn):
		self.EXECUTE_TIMEOUT = 3
		self.host = client_address[0]
		self.port = client_address[1]
		self.conn = client_conn
		self.os = None


	def recvall(self, timeout = None):
		result = ''
		self.conn.settimeout(timeout)
		while True:
			try:
				tmp = self.conn.recv(1024)
				if tmp == '':
					raise IOError("client lost")
				result += tmp
			except socket.error:
				break
		self.conn.settimeout(None)
		return result

	def recvuntil(self, pattern, timeout = None):
		result = ''
		self.conn.settimeout(timeout)
		while True:
			try:
				tmp = self.conn.recv(1)
				if tmp == '':
					raise IOError
				result += tmp
				if len(re.findall(pattern,result))>0:
					break
			except socket.error:
				log.waring('(%s:%s)timeout! return'%(self.host,self.port), __name__)
				break
		self.conn.settimeout(None)
		return result

	def info(self):
		return '%s:%s(%s)'%(self.host, self.port, self.os)

	def closeConn(self):
		try:
			self.conn.shutdown(socket.SHUT_RDWR)
			self.conn.close()
			return True
		except:
			return False

	def runCommand(self, command, timeout = 3):
		command, tag=comm_encode(command)
		log.debug('(%s:%s)raw command:%s'%(self.host,self.port, command), __name__)
		#clear the pipe prepare to recv execute result
		try:
			res = self.recvall(timeout=0)
			log.debug('(%s:%s)clear over!'%(self.host,self.port), __name__)
		except IOError as e:
			log.debug('(%s:%s)clear error! %s'%(self.host,self.port,e.message), __name__)
		
		try:
			log.debug('(%s:%s)send command'%(self.host,self.port), __name__)
			self.conn.sendall(command + '\n')
		except Exception as e:
			log.error('(%s:%s)connect lost!'%(self.host,self.port), __name__)
			return '[error]'

		try:
			log.debug('(%s:%s)recv result'%(self.host,self.port), __name__)
			result = self.recvuntil(r"%s[\s\S]*%s"%(tag,tag),timeout=timeout)
			if result.startswith(command):   #sometimes client repeat command back ,so we try to recv really result now
				result = self.recvuntil(r"%s[\s\S]*%s"%(tag,tag),timeout=timeout)
			if result== None:
				return '[error]'
		except IOError:
			log.error('(%s:%s)recv error, client lost!'%(self.host,self.port), __name__)
			return '[error]'

		try:
			result=res_decode(result,tag)
		except Exception as e:
			log.warning('(%s:%s)execute failed'%(self.host,self.port), __name__)
			log.debug('(%s:%s)[decode exception]%s'%(self.host,self.port,e.message), __name__)
			sys.stdout.flush()
			sys.stderr.flush()
			return '[error]'
		return result

	def __str__(self):
		return '%s:%s(%s)'%(self.host, self.port, self.os)

class BasicClient(Client):
	def __init__(self):
		Client.__init__(self,client_address, client_conn)