#!/usr/bin/env python
# -*- coding: utf-8 -*-

from time import sleep
import pickle 
import multiprocessing
import socket
import hashlib
import random
import string
import sys
import os
import re

from module.server import *
from module.client import *
from utils.log import Logger
from utils.submit import submit

reload(sys)
sys.setdefaultencoding(sys.getfilesystemencoding())

servers = []
target_servers = []


def list_command():
	print """Commands : 
              0. [h|help|?|\\n] : show this help
              1. [ls] : list all,'s' for server,'a' for all
              2. [la] : list all servers and clients
              3. [t] : set command target, format: [server]:clients, ([server]:clients),...
              			 ('a' for all, example : t 1:a,2:1-3,a:1-5 ) 
              4. [lt] : list command target, 's' for server, 'a' for all
              5. [lta] : list  all target server and clients
              6. [gaf] : get all flag
              7. [c] : command for all
              8. [cronadd] : add crontab
              9. [crondel] : del crontab
              10. [cl] : command to log
              14. [ac] : auto connection
              15. [aac] : all node auto connction
              16. [nm] : listen another port
              17. [q] : exit"""

def start_servers(addresses):
	for address in addresses:
		servers.append(Server(address))
	if len(servers) > 0:
		#TODO info
		list_servers()
		return True
	else:
		#TODO error
		return False

def list_servers():
	if len(servers) == 0:
		#TODO info 'no server running,please start server!'
		return False
	for num, server in enumerate(servers):
		print '({}) {}\n{}'.format(num, server.info('detail'), "-" * 0x20)
	return True

def list_all_clients():
	for num, server in enumerate(servers):
		print '({}) {}'.format(num, server.info('brief'))
		if len(server.clients) == 0:
			print '└(no client in this server!)'
		else:
			for n,client in enumerate(server.clients):
				print '└({}) {}'.format(num, client.info('brief'))
		print "-" * 0x20

def set_target_servers(targets):
	target_servers = []
	if targets == "a":
		target_servers = servers
	else:
		targets = re.split('[, ]', targets)
		for i in targets:
			index_range = re.findall('(\d+)-(\d+)', i)
			if len(index_range)>0:
				start, end = map(int, index_range[0])
				target_servers.append(servers[start : end + 1])
			else:
				index = int(i)
				target_servers.append(servers[index])

def set_target_clients(server, targets):
	server.target_clients=[]
	if targets == "a":
		server.target_clients = server.clients
	else:
		targets = re.split('[, ]', targets)
		for i in targets:
			index_range = re.findall('(\d+)-(\d+)', i)
			if len(index_range)>0:
				start, end = map(int, index_range[0])
				server.target_clients.append(server.clients[start : end + 1])
			else:
				index = int(i)
				server.target_clients.append(server.clients[index])

def list_targer_client():
	for target_server in target_servers:
		print '{}'.format(target_server.info('brief'))
		for num, client in target_server.clients:
			print '└({}) {}'.format(num, client.info('brief'))
		print "-" * 0x20

def send_command(command):
	for target_server in target_servers:
		target_server.send_command(command)


def main():



	



