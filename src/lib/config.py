#!/usr/bin/env python
# -*- encoding: utf-8 -*-

import ConfigParser
import os

Raise = object()

class Config(object):
	def __init__(self, filename = None):
		self.rc = ConfigParser.RawConfigParser()
		if filename is None:
			if os.name == 'posix':
				filelist = ['/etc/paste.conf', os.path.expanduser('~/.pasteconf'), './.pasteconf']
			else:
				filelist = [os.path.expanduser('~/.pasteconf'), './.pasteconf']
			self.rc.read(filelist)
		else:
			if not self.rc.read(filename):
				raise IOError('%s is not readable!' % filename)
		
	def get(self, path, default=None):
		try:
			section, entry = path.rsplit('.', 1)
		except ValueError:
			section = 'DEFAULT'
			entry	= path
		
		if section.lower() == 'default'	:
			section = 'DEFAULT'
		if section != 'DEFAULT' and not self.rc.has_section(section):
			if default is not Raise:
				return default
			raise KeyError('No such section: ' + section)
		try:
			return self.rc.get(section, entry)
		except ConfigParser.NoOptionError as e:
			raise KeyError(e)
		
	def getint(self, path, default=None):
		try:
			section, entry = path.rsplit('.', 1)
		except ValueError:
			section = 'DEFAULT'
			entry	= path
		
		if section.lower() == 'default'	:
			section = 'DEFAULT'
		if section != 'DEFAULT' and not self.rc.has_section(section):
			if default is not Raise:
				return default
			raise KeyError('No such section: ' + section)
		try:
			return int(self.rc.get(section, entry))
		except ConfigParser.NoOptionError as e:
			raise KeyError(e)
		except ValueError:
			raise
		
	def getfloat(self, path, default=None):
		try:
			section, entry = path.rsplit('.', 1)
		except ValueError:
			section = 'DEFAULT'
			entry	= path
		
		if section.lower() == 'default'	:
			section = 'DEFAULT'
		if section != 'DEFAULT' and not self.rc.has_section(section):
			if default is not Raise:
				return default
			raise KeyError('No such section: ' + section)
		try:
			return self.rc.get(section, entry)
		except ConfigParser.NoOptionError as e:
			raise KeyError(e)
		
	def getboolean(self, path, default=None):		
		try:
			section, entry = path.rsplit('.', 1)
		except ValueError:
			section = 'DEFAULT'
			entry	= path
		
		if section.lower() == 'default'	:
			section = 'DEFAULT'
		if section != 'DEFAULT' and not self.rc.has_section(section):
			if default is not Raise:
				return default
			raise KeyError('No such section: ' + section)
		try:
			val = self.rc.get(section, entry).lower()
		except ConfigParser.NoOptionError as e:
			raise KeyError(e)
		
		if val in ['1', 'yes', 'true', 'on']:
			return True
		if val in ['0', 'no', 'false', 'off']:
			return False
		
		raise ValueError(val + ' is True or False?')
	
	def getsection(self, section):
		if section.lower() == 'default'	:
			section = 'DEFAULT'
		if section != 'DEFAULT' and not self.rc.has_section(section):
			raise KeyError('No such section: ' + section)
		return dict(self.rc.items(section))
	
	def set(self, path, val):
		try:
			section, entry = path.rsplit('.', 1)
		except ValueError:
			section	= 'DEFAULT'
			entry	= path
			
		if section.lower() == 'default':
			section = 'DEFAULT'
		if section != 'DEFAULT' and not self.rc.has_section(section):
			self.rc.add_section(section)
		if isinstance(val, str):
			self.rc.set(section, entry, val)
		elif isinstance(val, unicode):
			self.rc.set(section, entry, val.encode('UTF-8'))
		elif isinstance(val, (int, float, long)):
			self.rc.set(section, entry, str(val))
		else:
			raise ValueError('Invalid type for val')
