#!/usr/bin/env python
# -*- encoding: utf-8 -*-
import argparse
import getpass
import json
import os
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
		opt_opt = opt.add_argument_group('Options')
		opt_opt.add_argument('-c', '--check', action='store_const', dest='check', default=True, const=True,
							 help='If stored oauth token is invalid, the process will be interrupted. (Default)')
		opt_opt.add_argument('-n', '--no-check', action='store_const', dest='check', const=False,
							 help='Process anonymously if stored oauth token is invalid.')
		action_push = opt_action.add_parser('push', help='Push one or more file to gist.', add_help=False)
		push_args = action_push.add_argument_group('Arguments')
		push_opts = action_push.add_argument_group('Options')
		push_opts.add_argument('-h', '--help', help='Print this help message and exit.', action='help')
		push_opts.add_argument('-a', '--anonymous', help='Post gist anonymously.', dest='gist.auth',
								action='store_const', const=False)
		push_opts.add_argument('-p', '--private', help='Hide this gist from search engine.', dest='private',
							    action='store_const', const=True, default=False)
		push_opts.add_argument('-d', '--description', help='Add a description for the gist.', dest='description',
							    default='Gist by paste.py @ ' + str(datetime.datetime.now()), metavar='DESCRIPTION')
		push_args.add_argument('files', nargs='*', metavar='files', help='Files to paste to gist, "-" or ignore to read from stdin.',
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
		auth_opts.add_argument('-r', '--remove', help='Remove stored authentication information.',
							   action='store_const', dest='remove', default=False, const=True)
		auth_opts.add_argument('-f', '--force', help='Force renew token, even if it is still valid.',
							   action='store_const', dest='force', default=False, const=True)
	
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
		conf = config.getConfig()
		res = self._do_auth()
		if res is not None:
			if not res:
				if conf.getboolean('check', True):
					print 'Token is invalid, please use paste.py gist auth to get a new token.'
					sys.exit(1)
				else:
					del self.req.headers['Authorization']
		files = conf.require('files')
		if files.count(sys.stdin) > 1:
			raise exception.InvalidValue('stdin was listed more than once!')
		logger.debug('private: ' + ('yes' if conf.require('private') else 'no'))
		logger.debug('description: ' + conf.require('description'))
		logger.debug('files: ' + str(len(files)))
		post_data = {
			'public'		: not conf.require('private'),
			'description'	: conf.require('description'),
		}
		file_data = dict()
		try:
			for file in files:
				logger.info('reading file ' + file.name)
				if file is sys.stdin:
					print 'Type your content here, end with EOF'
					print 'Use Ctrl-C to interrupt, if you have mistyped something.'
				content = file.read()
				logger.debug('file ' + file.name + ': %d lines, %d bytes' % (content.count('\n'), len(content)))
				fname = os.path.basename(file.name)
				now = 2
				if fname in file_data:
					if '.' in fname:
						name, ext = fname.rsplit('.', 1)
					else:
						name, ext = fname, ''
					while (name + '-' + str(now) + '.' + ext) in file_data:
						now += 1
					fname = (name + '-' + str(now) + '.' + ext)
				logger.debug('final filename: ' + fname)
				file_data[fname] = {
					'content'	: content,
				}
		except KeyboardInterrupt:
			logger.warn('Ctrl-C received, exiting.')
			sys.exit(1)
		post_data['files'] = file_data
		post_str = json.dumps(post_data)
		post_url = _api_base + '/gists'
		logger.debug('post url: ' + post_url)
		try:
			resp = self.req.post(post_url, data=post_str, headers={
				'Content-Type'	: 'application/json',
			})
		except exceptions.RequestException as e:
			logger.error('Post error: ' + e.message)
			raise exception.ServerException(e)
		logger.debug('http ok.')
		logger.info('server response: %d %s' % (resp.status_code, resp.reason))
		if resp.status_code == 201:
			logger.info('gist created')
			url = resp.json()[u'html_url']
			gistid = url.rsplit('/', 1)[1]
			print 'HTTP Link: ' + url
			print 'Paste.py uri: gist://' + gistid
		else:
			raise exception.ServerException('Server responsed with unknown status: %d %s ' % (resp.status_code, resp.reason))
	
	@action('pull')
	def pull(self):
		# TODO: Implements pull
		print 'Still a stub :('
		sys.exit(1)
	
	@action('auth')
	def write_auth(self):
		# TODO: Implements auth
		conf = config.getConfig()
		fileconf = config.getGlobalConfig() if conf.require('global') else config.getUserConfig()
		remove = conf.require('remove')
		if remove:
			fileconf.remove('gist.auth')
			fileconf.remove('gist.token')
			print 'Authentication removed, you may delete the token from your user panel.'
			return
		if fileconf.get('gist.auth', False) and not conf.get('force', False):
			logger.info('check current token')
			try:
				token = fileconf.require('gist.token')
			except exception.NoSuchOption:
				fileconf.remove('gist.auth')
				return self.write_auth()
			result = self._do_auth(token=token)
			if result:
				print 'Current token is valid, no auth required.'
				return
			print 'Current token is invalid, requesting a new token.'
		token = self._perform_auth()
		logger.info('auth ok.')
		fileconf.set('gist.auth', True)
		fileconf.set('gist.token', token)
		logger.debug('saving to config file.')
		fileconf.save()
		print 'Done!'
	
	def _perform_auth(self, otp_token=None):
		if otp_token is None:
			try:
				self.user = raw_input('Username: ')
				logger.debug('user: ' + self.user)
				self.pwd = getpass.getpass('Password: ')
				logger.debug('password ok.')
			except KeyboardInterrupt:
				logger.warn('Ctrl-C detected.')
				sys.exit(1)
		user = self.user
		pwd = self.pwd
		logger.info('auth: fetch new token')
		post_json = {
			'scopes'	: ['gist'],
			'note'		: 'paste.py @ ' + str(datetime.datetime.now()),
			'note_url'	: 'https://github.com/jackyyf/paste.py',
		}
		post_headers = {
			'Content-Type'	: 'application/json',
		}
		if otp_token is not None:
			post_headers['X-GitHub-OTP'] = otp_token
		post_str = json.dumps(post_json)
		post_url = _api_base + '/authorizations'
		logger.debug('post_url: ' + post_url)
		try:
			resp = self.req.post(post_url, data=post_str, headers=post_headers, auth=(user, pwd))
		except exceptions.RequestException as e:
			raise exception.ServerException(e)
		logger.info('http ok. response: %d %s' % (resp.status_code, resp.reason))
		if resp.status_code == 201:
			logger.info('auth ok.')
			token = resp.json()[u'token']
			logger.debug(resp.content)
			self.req.headers['Authorization'] = 'token ' + token
			return token
		elif resp.status_code == 401:
			# Two factor auth?
			logger.warn('auth failed')
			if 'X-GitHub-OTP' in resp.headers:
				logger.warn('auth: two-factor required')
				try:
					token = raw_input('Two factor token from ' + resp.headers['X-Github-OTP'].replace('required; ', '') + ':')
				except KeyboardInterrupt:
					logger.warn('Ctrl-C detected')
					sys.exit(1)
				return self._perform_auth(otp_token=token)
			else:
				logger.error('username or password error.')
				return self._perform_auth()
		else:
			raise exception.ServerException('Server responsed with unknown status: %d %s' % (resp.status_code, resp.reason))
		
	
	def _do_auth(self, token=None):
		# Authenticate to github, save some login info (user/pass, or oauth token)
		conf = config.getConfig()
		auth = conf.getboolean('gist.auth', False) or token is not None
		if auth: # User/Pass Pair
			logger.info('auth: oauth token')
			if token is None:
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
				return False
			elif resp.status_code == 200:
				logger.info('token ok.')
				return True
			else:
				logger.warn('unknown response status: %d %s' % (resp.status_code, resp.reason))
				raise exception.ServerException('Server responsed with unknown status: %d %s' % (resp.status_code, resp.reason))
		logger.info('auth: none')
		return None
