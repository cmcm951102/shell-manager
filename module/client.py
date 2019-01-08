#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
sys.path.append('../')
from utils import log
from time import sleep
import socket
import string
import random

def random_string(length, chars=(string.letters + string.digits)):
    return "".join([random.choice(chars) for i in range(length)])

class Client():
	def __init__(self, client_address, client_conn):
		self.EXECUTE_TIMEOUT = 3
		self.host = client_address[0]
		self.port = client_address[1]
		self.conn = client_conn
		self.os = None

	def recvall(self, max_null_times = 3):
		result = ''
		null_time = 0
		while True:
			try:
				tmp = self.conn.recv(1024)
				if tmp == '':
					null_time += 1
					if null_time > max_null_times:
						raise IOError('recv error')
					else:
						continue
				result += tmp
				if len(tmp) < 1024:
					break
			except socket.error:
				break
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

	def runCommand(self, command):
		tag=random_string(8)
		command='echo %s && %s && echo %s'%(tag,command.strip(),tag)
		log.debug('(%s:%s)raw command:%s'%(self.host,self.port, command), __name__)
		#clear the pipe
		try:
			self.conn.settimeout(0.5)
			self.recvall()
		except IOError:
			log.debug('(%s:%s)clear error!'%(self.host,self.port), __name__)
		except socket.error:
			log.debug('(%s:%s)clear over!'%(self.host,self.port), __name__)
		finally:
			self.conn.settimeout(self.EXECUTE_TIMEOUT)

		try:
			self.conn.sendall(command + '\n')
		except Exception as e:
			log.error('(%s:%s)connect lost!'%(self.host,self.port), __name__)
			return '[error]'

		sleep(0.5)
		try:
			result = self.recvall()
		except IOError:
			log.error('(%s:%s)recv error!'%(self.host,self.port), __name__)
		finally:
			if result.strip().startswith(command):
				result=result.replace(command, '')
			if len(result.split(tag)) == 3:
				result = result.split(tag)[1].strip()
			else:
				log.warning('(%s:%s)execute failed'%(self.host,self.port), __name__)
				log.debug('(%s:%s)raw result:\n%s'%(self.host,self.port,result), __name__)
				result = '[error]'
			return result

	def __str__(self):
		return '%s:%s(%s)'%(self.host, self.port, self.os)

class BasicClient(Client):
	def __init__(self):
		Client.__init__(self,client_address, client_conn)