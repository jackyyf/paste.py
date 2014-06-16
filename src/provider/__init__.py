#!/usr/bin/env python
# -*- encoding: utf-8 -*-

import argparse

protocols = dict()

class ProviderBase(object):
	
	def register_protocol(self, proto_name, ignore_conflict=False):
		'''
		:param proto_name: str Protocol prefix for provider wants to register. Eg: 'ubuntu' if you want to handle 'ubuntu:1234567'.
							   Allowed characters are [a-zA-Z0-9_\-], note protocol is case INSENSITIVE.
		:return: None
		'''
		valid_chars = 'abcdefghijklmnopqrstuvwxyz0123456789_-'
		if not isinstance(proto_name, (str, unicode)):
			raise ValueError('proto_name should be a string.')
		proto_name = proto_name.lower()
		for ch in proto_name:
			if ch not in valid_chars:
				raise ValueError('Invalid char %s in proto_name' % ch)
			
		global protocols
		
		if proto_name in protocols:
			if ignore_conflict:
				return False
			raise KeyError('proto_name is already registered by %s' % protocols[proto_name].__class__.__name__)
		
		protocols[proto_name] = self
	
	def add_push_args(self, opt):
		'''
		Add provider specific argument for push action.
		:param opt: argparse._ArgumentGroup An option group for you to add arguments.
		:return: None
		'''
		raise NotImplementedError('add_push_args should be implemented!')
	
	def add_pull_args(self, opt):
		'''
		Add provider specific argument for pull action.
		:param opt: argparse._ArgumentGroup An option group for you to add arguments.
		:return: None
		'''
		raise NotImplementedError('add_pull_args should be implemented!')