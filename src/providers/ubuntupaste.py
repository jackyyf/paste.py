import argparse
import os
import requests
from requests import exceptions
import sys

from lib.provider import ProviderBase
from common import exception
from lib import logger, uri, config

import getpass
import urllib
import re
# import pyquery
import HTMLParser

# Languages for highlighting!

_languages = {
	'c'			: 'c',
	'cpp'		: 'cpp',
	'cc'		: 'cpp',
	'cs'		: 'csharp',
	'sh'		: 'bash',
	'bash'		: 'bash',
	'aspx'		: 'aspx-cs',
	'diff'		: 'diff',
	'patch'		: 'diff',
	'go'		: 'go',
	'haml'		: 'haml',
	'hs'		: 'haskell',
	'html'		: 'html',
	'ini'		: 'int',
	'java'		: 'java',
	'js'		: 'js',
	'jsp'		: 'jsp',
	'lhs'		: 'lhs',
	'lua'		: 'lua',
	'sql'		: 'sql',
	'as'		: 'nasm',
	'pas'		: 'delphi',
	'pp'		: 'delphi',
	'pl'		: 'perl',
	'php'		: 'php',
	'ps'		: 'postscript',
	'pot'		: 'pot',
	'py'		: 'python',
	'py3'		: 'python3',
	'rb'		: 'ruby',
	'rst'		: 'rst',
	'tcl'		: 'tcl',
	'sqlite'	: 'sqlite3',
	'sqlite3'	: 'sqlite3',
	'tex'		: 'tex',
	'vim'		: 'vim',
	'xml'		: 'xml',
	'xslt'		: 'xslt',
	'yaml'		: 'yaml',
	'yml'		: 'yml',
}

_default = 'text'

def _get_language(filename):
	if filename.count('.') < 1:
		logger.info('No suffix in filename. Text assumed.')
		return _default
	suffix = filename.rsplit('.', 1)[1]
	logger.info('filename suffix: ' + suffix)
	return _languages.get(suffix.lower(), _default)

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
	
class UbuntuPaste(ProviderBase):
	
	_name = 'ubuntu'
	_info = 'Ubuntu paste (http://paste.ubuntu.com)'

	def __init__(self):
		logger.debug('call: ubuntupaste.__init__')
		self._actions = dict()
		self.req = requests.Session()
		logger.debug('http: set user-agent.')
		self.req.headers['User-Agent'] = config.full_version()
		super(UbuntuPaste, self).__init__()
		
	def add_args(self, opt):
		opt_action = opt.add_subparsers(title='Actions', metavar='action', dest='action')
		action_push = opt_action.add_parser('push', help='Push a file to ubuntu paste.', add_help=False)
		push_args = action_push.add_argument_group('Arguments')
		push_options = action_push.add_argument_group('Options')
		push_options.add_argument('-h', '--help', action='help', help='Print this help message and exit.')
		push_options.add_argument('-l', '--language', metavar='language', dest='ubuntupaste.lang',
						 help='Language for highlight.')
		push_args.add_argument(metavar='file', nargs='?', dest='src', help='File you want to push, - or ignore to read from stdin.',
								 type=argparse.FileType('r'), default='-')
		action_pull = opt_action.add_parser('pull', help='Pull a file from ubuntu paste.', add_help=False)
		pull_args = action_pull.add_argument_group('Arguments')
		pull_options = action_pull.add_argument_group('Options')
		pull_options.add_argument('-h', '--help', action='help', help='Print this help message and exit.')
		pull_options.add_argument('-f', '--force', action='store_const', dest='overrite', default=False, const=True,
								  help='Overwrite existing file.')
		pull_args.add_argument(metavar='pasteid', dest='src', help='Paste ID you want to pull from.')
		pull_args.add_argument(metavar='file', nargs='?', dest='dest', help='Local file you want to store at, - or ignore to write to stdout.',
							   default='-')
		
	def run(self):
		global _actions
		conf = config.getConfig()
		action = conf.require('action')
		if action not in _actions:
			logger.fatal('No function for action: ' + action)
		_actions[action](self)
		
	
	@staticmethod
	def html2text(content):
		# Reset prev pos.
		logger.debug('html: %d bytes, %d lines' % (len(content), content.count('\n')))
		start_pos	= 0
		while True:
			# Use prev pos
			start_pos = content.find('<', start_pos)
			logger.debug('start_pos: %d' % start_pos)
			if start_pos < 0:
				break
			end_pos = content.find('>', start_pos + 1)
			logger.debug('end_pos: %d' % end_pos)
			if end_pos < 0:
				raise exception.ServerException('Server responsed with invalid html. (Truncated response?)')
			content = content[:start_pos] + content[end_pos + 1:]
		content = HTMLParser.HTMLParser().unescape(content)
		logger.debug('text: %d bytes, %d lines' % (len(content), content.count('\n')))
		return content
	
	@staticmethod
	def fetch_between(content, start_flag, end_flag):
		start_len, end_len	= len(start_flag), len(end_flag)
		start_pos	= content.find(start_flag)
		logger.debug('start_pos: %d' % start_pos)
		if start_pos < 0:
			raise exception.ServerException('Start flag not found!')
		end_pos		= content.find(end_flag, start_pos + start_len)
		logger.debug('end_pos: %d' % end_pos)
		if end_pos < 0:
			raise exception.ServerException('End flag not found!')
		return content[start_pos + start_len : end_pos]
	
	@action('push')
	def push_content(self):
		logger.debug('call: ubuntupaste.push_content')
		conf = config.getConfig()
		post_target	= 'http://paste.ubuntu.com/'
		logger.debug('post target: ' + post_target)
		poster		= conf.get('ubuntu.user', getpass.getuser())
		logger.debug('poster: ' + poster)
		# Get Filename for highlight.
		filename	= conf.require('src').name
		if filename == '-':
			print 'Type your content here, end with EOF'
			print 'Use Ctrl-C to interrupt, if you have mistyped something.'
		try:
			content = conf.require('src').read()
		except KeyboardInterrupt:
			logger.warn('Ctrl-C received, interrpted...')
			sys.exit(1)
		lines = content.count('\n')
		bytes = len(content)
		logger.info('content: %d lines, %d bytes' % (lines, bytes))
		lang = conf.get('ubuntu.lang', _get_language(filename))
		logger.debug('highlight: ' + lang)
		post_data	= {
			'poster'	: poster,
			'syntax'	: lang,
			'content'	: content,
		}
		try:
			resp = self.req.post(post_target, data=post_data, allow_redirects=False)
		except exceptions.RequestException as e:
			logger.info('Exception: ' + e.__class__.__name__)
			logger.error('Something went wrong when communicating with paste.ubuntu.com!')
			raise exception.ServerException(e)
			
		logger.debug('HTTP OK')
		logger.info('HTTP Status: %d %s' % (resp.status_code, resp.reason))
		
		if resp.status_code == 302:
			pastepad = resp.headers['location']
			logger.debug('location: ' + pastepad)
			pattern	= re.compile(r'^http:\/\/paste.ubuntu.com/(?P<paste_id>\d+)/$')
			res = pattern.match(pastepad)
			if not res:
				raise exception.ServerException('Unknown location: ' + pastepad)
			paste_id = res.group('paste_id')
			logger.info('paste_id: ' + paste_id)
			# return paste_id
			print 'Paste ID: ' + str(paste_id)
			print 'HTTP Link: ' + pastepad
			return
		
		if resp.status_code == 200:
			data = resp.content
			err_start_flag = '<ul class="errorlist"><li>'
			err_stop_flag = '</li></ul>'
			msg = self.html2text(self.fetch_between(resp.content, err_start_flag, err_stop_flag))
			raise exception.ServerException('Server refused our paste: ' + msg)
			
		raise exception.ServerException('Server responsed with unknown status %d %s' % (resp.status_code, resp.reason))
		
	@action('pull')
	def pull_content(self):
		logger.debug('call: ubuntupaste.pull_content')
		conf = config.getConfig()
		fn = conf.require('dest')
		if fn == '-':
			fo = sys.stdout
		else:
			if os.path.exists(fn):
				if not conf.get('overwrite', False):
					raise exception.FileExists('File %s already exists.' % fn)
			fo = open(fn, 'w')
		_uri = conf.require('src')
		res = uri.parse(_uri)
		if res is None:
			raise exception.InvalidURI('Invalid URI: ' + _uri)
		logger.debug('uri format ok.')
		logger.debug('scheme: ' + res.scheme)
		if res.scheme == 'ubuntu':
			logger.info('using ubuntu:// style uri')
			pid = res.path
			logger.debug('path: ' + pid)
			for ch in pid:
				if not ch.isdigit():
					raise exception.InvalidURI('UbuntuPaste should only contains digits!')
			
			if pid != str(int(pid)):
				raise exception.InvalidURI('No leading zero allowed.')
		
			url = 'http://paste.ubuntu.com/{pid}/'.format(pid=pid)
			logger.info('to http url: ' + url)
		elif res.scheme == 'http':
			logger.info('using http:// style uri')
			if '/' not in res.path:
				raise exception.InvalidURI('Invalid http url: ' + _uri)
			host, path = map(lambda x : x.lower(), res.path.split('/', 1))
			# NOTE: Leading / in path is removed when using split.
			logger.debug('http host: ' + host)
			logger.debug('http path: ' + path)
			if host != 'paste.ubuntu.com':
				raise exception.InvalidURI('HTTP Host should be paste.ubuntu.com!')
			pattern = re.compile(r'^[1-9](?:\d+)(?:/?)')
			if not pattern.match(path):
				raise exception.InvalidURI('Invalid path for ubuntu paste!')
			
			# url validated.
			url = _uri
		else:
			raise exception.InvalidURI('Unknown scheme: ' + res.scheme)
		
		# Check if pad exists
		try:
			res = self.req.get(url)
		except exceptions.RequestException as e:
			logger.info('Exception: ' + e.__class__.__name__)
			logger.warn('Something wrong when communicating with paste.ubuntu.com, assume paste pad exists.')
			return url
		
		logger.debug('HTTP OK.')
		logger.info('Server response: %d %s' % (res.status_code, res.reason))
		
		if res.status_code == 200: # OK
			# Q = pyquery.PyQuery(res.content)
			# content	= pyquery.PyQuery(Q('.code').html().replace('\n', '<br />')).text()#
			start_flag	= '<td class="code"><div class="paste"><pre>'
			end_flag	= '</pre></div>'

			content		= self.html2text(self.fetch_between(res.content, start_flag, end_flag))
			logger.debug('content: %d lines, %d bytes' % (content.count('\n') + 1, len(content)))
			# return content
			fo.write(content)
			return
		
		if res.status_code >= 400 and res.status_code < 500:
			raise exception.NoSuchPad('No such pad: %s. Server responsed with status code %d' % (_uri, res.status_code))
		
		raise exception.ServerException('Server responsed with status code %d' % res.status_code)
		
