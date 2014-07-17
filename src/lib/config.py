#!/usr/bin/env python
# -*- encoding: utf-8 -*-

_version = (0, 0, 1)
_name = 'Paste.py'

import ConfigParser
import os
import sys
from common import exception
from lib import logger

def version():
	return '.'.join(map(str, _version))

def version_tuple():
	return _version[:]

def full_version():
	return _name + '/' + version()

Raise = object()

_global_filename = '/etc/paste.conf'
_user_filename = os.path.expanduser('~/.pasterc')

class FileConfig(object):
	def __init__(self, filename = None):
		self.rc = ConfigParser.RawConfigParser()
		if filename is None:
			if os.name == 'posix':
				filelist = [_global_filename, _user_filename]
			else:
				filelist = [_user_filename]
			self.rc.read(filelist)
		else:
			self.rc.read(filename)
		self._filename = filename
		
	def get(self, path, default=None):
		logger.debug('config get: ' + path)
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
		
	def require(self, path):
		return self.get(path, default=Raise)
		
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
		val = self.get(path, default)
		if val is default:
			return val
		
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
		logger.debug('config set: %s=%r' % (path, val))
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
			self.rc.set(section, entry, '1' if val else '0')
		else:
			raise ValueError('Invalid type for val')
		
	def remove(self, path, check=False):
		logger.debug('remove key: ' + path)
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
		
	def save(self):
		if not isinstance(self._filename, (str, unicode)):
			raise ValueError('Invalid filename.')
		logger.info('saving to ' + self._filename)
		with open(self._filename, 'w') as f:
			self.saveTo(f)
		
	def dump(self, fd=sys.stderr):
		for section in self.rc.sections() + ['DEFAULT']:
			print >>fd, 'Section ' + section
			for k, v in self.rc.items(section):
				print >>fd, 'Option %s=%s' % (k, str(v))
			print >>fd, 'EndSection'
			print >>fd
			
		print >>fd, '===================='
			
		
class RuntimeConfig(FileConfig):
	
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
			
		self.rc.set(section, entry, val)
		
	def saveTo(self, fd):
		raise NotImplementedError('RuntimeConfig contains not serializable information.')
		
			
_instance = None
_global_instance = None
_user_instance = None
		
def getConfig():
	global _instance
	if _instance is None:
		logger.debug('creating config instance')
		_instance = RuntimeConfig()
	return _instance

def getGlobalConfig():
	if os.name != 'posix':
		raise OSError('No global config supported in your platform, currently only posix are supported.')
	global _global_instance
	if _global_instance is None:
		logger.debug('opening global config')
		_global_instance = FileConfig(_global_filename)
	return _global_instance

def getUserConfig():
	global  _user_instance
	if _user_instance is None:
		logger.debug('opening user config')
		_user_instance = FileConfig(_user_filename)
	return _user_instance
	