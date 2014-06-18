#!/usr/bin/env python
# -*- encoding: utf-8 -*-

import ConfigParser
import os
from common import exception

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
			if default is Raise:
				raise exception.NoSuchOption('No such section: ' + section)
			return default
		try:
			return self.rc.get(section, entry)
		except ConfigParser.NoOptionError as e:
			if default is Raise:
				raise exception.NoSuchOption(e)
			return default
		
	def getint(self, path, default=None):
		try:
			return int(self.get(path, default))
		except ValueError as e:
			if default is Raise:
				raise exception.InvalidValue(e)
			return default
		
	def getfloat(self, path, default=None):
		try:
			return float(self.get(path, default))
		except ValueError as e:
			if default is Raise:
				raise exception.InvalidValue(e)
			return default
			
		
	def getboolean(self, path, default=None):		
		val = self.get(path, default).lower()
		
		if val in ['1', 'yes', 'true', 'on', 'y']:
			return True
		if val in ['0', 'no', 'false', 'off', 'n']:
			return False
		
		if default is Raise:
			raise exception.InvalidValue(val + ' is True or False?')
		return default
	
	def getsection(self, section):
		if section.lower() == 'default'	:
			section = 'DEFAULT'
		if section != 'DEFAULT' and not self.rc.has_section(section):
			raise exception.NoSuchOption(section)
		return dict(self.rc.items(section))
	
	def set(self, path, val):
		if val is None: # Do not change.
			return
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
		elif isinstance(val, bool):
			self.rc.set(section, entry, '1')
		else:
			raise ValueError('Invalid type for val')
		
	def remove(self, path, check=False):
		try:
			section, entry = path.rsplit('.', 1)
		except ValueError:
			section	= 'DEFAULT'
			entry	= path
			
		if section.lower() == 'default':
			section = 'DEFAULT'

		if section != 'DEFAULT' and not self.rc.has_section(section):
			if check:
				raise exception.NoSuchOption('No such section: ' + section)
			return
		
		res = self.rc.remove_option(section, entry)
		if check and not res:
			raise exception.NoSuchOption('No such config entry: ' + path)
		
		return res
	
	def saveTo(self, fd):
		self.rc.write(fd)
		
			
_instance = None
		
def getConfig():
	global _instance
	if _instance is None:
		_instance = Config()
	return _instance