#!/usr/bin/env python
# -*- encoding: utf-8 -*-

from lib.provider import ProviderBase
from common import exception
from lib import logger, uri, config

class Gist(ProviderBase):
	_name = 'gist'
	_info = 'Github gist (https://gist.github.com)'
	def __init__(self):
		logger.debug('call: gist.__init__')
		super(Gist, self).__init__()

	def add_args(self, opt):
		pass