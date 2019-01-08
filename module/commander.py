#!/usr/bin/env python
# -*- coding: utf-8 -*-

import socket
from time import sleep
from threading import Thread, Lock, Condition
import sys
sys.path.append('../')
from utils import log
from Queue import Queue

class Commander():
	def __init__(self,  server, commander_listen_address):
		self.server=server
		self.commander_listen_address = commander_listen_address
		self.conn=None
		self.conn_lock=Lock()
		self.socket=None
		self.command_prompt='>>'
		self.CLEAN_INTERVAL_TIME=5

		self.buf=''
		self.command_queue=Queue()
		self.listener=Thread(target=self._listen)
		self.listener.setDaemon(True)
		self.listener.start()
		self._binded_condition=Condition()
		self._waitBind()
		log.info('command server is listening on %s:%s'%(self.commander_listen_address), __name__)
		self.console=Thread(target=self._console)
		self.console.setDaemon(True)
		self.console.start()
		

	def _bindedNotify(self):
		self._binded_condition.acquire()
		self._binded_condition.notifyAll()
		self._binded_condition.release()

	def _waitBind(self):
		self._binded_condition.acquire()
		self._binded_condition.wait()
		self._binded_condition.release()

	def _console(self):
		while True:
			command=raw_input('[%s]%s'%(self.server.info('t br'),self.command_prompt)).strip()
			self.command_queue.put(command)
			self.server.waitExecute()


	def _listen(self):
		self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		self.socket.bind(self.commander_listen_address)
		self.commander_listen_address=self.socket.getsockname()
		self.socket.listen(1)
		self._bindedNotify()
		while True:
			if self.conn == None:
				new_conn,addr = self.socket.accept()
				log.info('commander on %s:%s connected'%addr, __name__)
				self.conn_lock.acquire()
				self.conn = new_conn
				self.conn_lock.release()

			tmp = self.conn.recv(100)
			if tmp == '':
				log.warning('connect lost...', __name__)
				self.conn_lock.acquire()
				self.conn = None
				self.conn_lock.release()
			else:
				self.buf += tmp
				commands = self.buf.split('\n')
				for i in commands[:-1]:
					if i.strip() != '':
						self.command_queue.put(i.strip())
				self.buf = commands[-1]

	def getCommand(self):
		return self.command_queue.get()

	def sendResult(self,result):
		if self.conn != None:
			self.conn_lock.acquire()
			try:
				self.conn.sendall(result)
				succ = True
			except:
				log.error('connect lost!', __name__)
				self.conn = None
				succ = False
			finally:
				self.conn_lock.release()
		print '%s'%result