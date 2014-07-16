#!/usr/bin/env python
# -*- encoding: utf-8 -*-
import argparse
import getpass
import sys
import datetime

from lib.provider import ProviderBase
from common import exception
from lib import logger, uri, config

import requests
from requests import exceptions

_no_validate = lambda _=None : _

def to_bool(val):
	val = val.lower()
	if val in ['1', 'yes', 'true', 'on', 'y']:
		return True
	if val in ['0', 'no', 'false', 'off', 'n']:
		return False
	raise ValueError('Invalid bool value: ' + val)

_api_base = 'https://api.github.com'

# For future use: config part.
_config_entry = {
	# You may add more entries here.
	# Value can be two types : a list or a validator.
	# If value is a list, user provided value should be one of the element in the list.
	# Otherwise, value is validated by call the validator with the value,
	#   if no exception raised, the returned value is used.
	#   if all values are accepted, use _no_validate
	# 'auth'	: ['anonymous', 'basic'],
	'auth'		: to_bool,
	'token'		: _no_validate,
}

_actions = dict()

def action(action_name):
	def _add(func):
		global _actions
		logger.debug('decorator: add_action ' + action_name)
		if action_name in _actions:
			logger.fatal(action_name + ' already registered!')
		_actions[action_name] = func
		return func
	return _add
	
class Gist(ProviderBase):
	_name = 'gist'
	_info = 'Github gist (https://gist.github.com)'
	def __init__(self):
		logger.debug('call: gist.__init__')
		self.req = requests.Session()
		logger.debug('http: set user-agent.')
		self.req.headers['User-Agent'] = config.full_version()
		self.req.headers['Accept'] = 'application/vnd.github.v3+json'
		super(Gist, self).__init__()

	def add_args(self, opt):
		opt_action = opt.add_subparsers(title='Actions', metavar='action', dest='action')
		action_push = opt_action.add_parser('push', help='Push one or more file to gist.', add_help=False)
		push_args = action_push.add_argument_group('Arguments')
		push_opts = action_push.add_argument_group('Options')
		push_opts.add_argument('-h', '--help', help='Print this help message and exit.', action='help')
		push_opts.add_argument('-a', '--anonymous', help='Post gist anonymously.', dest='gist.auth',
								action='store_const', const=False)
		push_args.add_argument('src', nargs='*', metavar='files', help='Files to paste to gist, "-" or ignore to read from stdin.',
								type=argparse.FileType('r'), default=[sys.stdin])
		action_pull = opt_action.add_parser('pull', help='Pull one or more file from gist.', add_help=False)
		pull_args = action_pull.add_argument_group('Arguments')
		pull_opts = action_pull.add_argument_group('Options')
		pull_opts.add_argument('-h', '--help', action='help', help='Print this help message and exit.')
		pull_opts.add_argument('-f', '--files', help='Specify files you want to pull, may use src=dest to specify local file destination.',
								dest='files', nargs='*', default=[])
		pull_args.add_argument('url', help='Gist url, you may use http link or gist://gistid. '
							   'Note: with gist://gistid format, there are some easy ways to download specific files without -f '
							   'you can use gist://gistid?remote_name=local_name&remote_name2, which assumes remote_name2=remote_name2. '
							   '`remote_name` and `local_name` should be quoted with urllib.quote')
		action_auth = opt_action.add_parser('auth', help='Add new or modify current authentication info for gist.', add_help=False)
		auth_opts = action_auth.add_argument_group('Options')
		auth_opts.add_argument('-h', '--help', help='Print this help message and exit.', action='help')
		auth_opts.add_argument('-s', '--system', help='Add to system wide config file (/etc/paste.conf), instead of current user (~/.pasterc)',
							   action='store_const', dest='global', default=False, const=True)
		auth_opts.add_argument('-l', '--login', help='Store username/password pair, and login each time you push/pull, instead of oauth token (Not recommended.)',
							   action='store_const', dest='mode', default='oauth', const='basic')
		auth_opts.add_argument('-r', '--remove', help='Remove stored authentication information.',
							   action='store_const', dest='remove', default=False, const=True)
	
	def run(self):
		global _actions
		conf = config.getConfig()
		action = conf.require('action')
		if action not in _actions:
			logger.fatal('No function for action: ' + action)
		_actions[action](self)
		
	@action('push')
	def push(self):
		# TODO: Implements push.
		pass
	
	@action('pull')
	def pull(self):
		# TODO: Implements pull
		pass
	
	@action('auth')
	def write_auth(self):
		# TODO: Implements auth
		pass
	
	def _perform_auth(self):
		user = raw_input('Username: ')
		logger.debug('user: ' + user)
		pwd = getpass.getpass('Password: ')
		logger.debug('password ok.')
		logger.info('auth: fetch new token')
		post_json = {
			'scopes' : ['gist'],
			'note' : 'paste.py @ ' + str(datetime.datetime.now())
		}
	
	def _do_auth(self):
		# Authenticate to github, save some login info (user/pass, or oauth token)
		conf = config.getConfig()
		auth = conf.getboolean('gist.auth', False)
		if auth: # User/Pass Pair
			logger.info('auth: oauth token')
			token = conf.require('gist.token')
			logger.debug('auth: test token usability')
			# Try authenticate
			self.req.headers['Authorization'] = 'token ' + token
			# Get a time in future (1 year)
			fmt_time = (datetime.datetime.now() + datetime.timedelta(days=365)).strftime('%Y-%m-%dT%H:%M:%SZ')
			test_url = _api_base + '/gists?since=' + fmt_time
			logger.debug('test url: ' + test_url)
			try:
				resp = self.req.get(test_url)
			except exceptions.RequestException as e:
				logger.warn('http error, assume token is good.')
				logger.info('[%s] %s' % (e.__class__.__name__, e.message))
				return
			logger.debug('http ok, response: %d %s' % (resp.status_code, resp.reason))
			if resp.status_code == 401: # Invalid token
				logger.warn('invalid token')
				self._perform_auth()
				return
			elif resp.status_code == 200:
				logger.info('token ok.')
				return
			else:
				logger.warn('unknown response status: %d %s' % (resp.status_code, resp.reason))
				raise exception.ServerException('Server responsed with unknown status: %d %s' % (resp.status_code, resp.reason))
		logger.info('auth: none')
