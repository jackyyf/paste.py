#!/usr/bin/env python
# -*- encoding: utf-8 -*-

from common import exception
from lib import uri, logger

providers = dict()

class ProviderBase(object):
	
	_name = 'provider_name'
	_info = 'One line introduction for this provider.'
	
	def __init__(self):
		logger.debug('call: providerbase.__init__')
		logger.debug('register_provider: name=%s, class=%s' % (self._name, self.__class__.__name__))
		valid_chars = 'abcdefghijklmnopqrstuvwxyz0123456789_-'
		if not isinstance(self._name, (str, unicode)):
			raise ValueError('proto_name should be a string.')
		proto_name = self._name.lower()
		for ch in proto_name:
			if ch not in valid_chars:
				raise ValueError('Invalid char %s in proto_name' % ch)
			
		global providers
		
		if proto_name in providers:
			raise KeyError('provider is already registered by %s' % providers[proto_name].__class__.__name__)
		
		providers[proto_name] = self
		self._name	= proto_name
	
	def add_args(self, opt):
		'''
		Add provider specific argument for fetch action.
		:param opt: argparse.ArgumentParser A subparser for program to parse.
		:return: None
		'''
		raise NotImplementedError('add_args should be implemented!')
	
	def run(self):
		'''
		Main process of this provider.
		You may get data from config, which contains all information from config file and command line.
		:return: None
		'''
		raise NotImplementedError('run should be implemented!')
	
	
def getProvider(name):
	logger.debug('call: provider.getProvider: name=' + name)
	# name is processed by argparse, so it's safe to return it directly.
	return providers[name]
