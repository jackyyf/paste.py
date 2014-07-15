#!/usr/bin/env python
# -*- encoding: utf-8 -*-

import re
import urllib

pattern = re.compile(r'^(?P<scheme>[0-9a-z_\-]+):(?:\/\/)?(?P<path>.+?)(?:\?(?P<arg_str>.*))?$', re.IGNORECASE)

def parse(uri):
	if not isinstance(uri, str):
		return None
	result = pattern.match(uri)
	if not result:
		return None
	return URIResult(result.group('scheme'), result.group('path'), result.group('arg_str'))
	

class URIResult:
	def __init__(self, scheme, path, arg_str):
		self.scheme = scheme
		self.path = path
		arg_str = arg_str or ''
		args = arg_str.split('&')
		self.args = {}
		for arg in args:
			if '=' in arg:
				k, v = arg.split('=')
				self.args[urllib.unquote(k)] = urllib.unquote(v)
			else:
				self.args[urllib.unquote(arg)] = True
			
	def get_arg(self, key, default=None):
		return self.args.get(key, default)
	
	
