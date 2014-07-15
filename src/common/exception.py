#!/usr/bin/env python
# -*- encoding: utf-8 -*-

class Exception(BaseException):
	pass

class InvalidURI(Exception):
	pass

class NoSuchPad(Exception):
	pass

class ServerException(Exception):
	pass

class NoSuchOption(Exception):
	pass

class InvalidValue(Exception):
	pass

class NoProvider(Exception):
	pass

class DuplicateRegister(Exception):
	pass