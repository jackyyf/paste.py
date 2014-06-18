#!/usr/bin/env python
# -*- encoding: utf-8 -*-

class InvalidURI(BaseException):
	pass

class NoSuchPad(BaseException):
	pass

class ServerException(BaseException):
	pass

class NoSuchOption(BaseException):
	pass

class InvalidValue(BaseException):
	pass

class NoProvider(BaseException):
	pass