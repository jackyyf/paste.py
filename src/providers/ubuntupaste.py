import requests
from requests import exceptions

from lib.provider import ProviderBase
from common import exception
from lib import logger, uri, config

import getpass
import urllib
import re
import pyquery
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

class UbuntuPaste(ProviderBase):

	def __init__(self):
		logger.debug('call: ubuntupaste.__init__')
		self.register_protocol('ubuntu')
		
	def add_fetch_args(self, opt):
		pass
	
	def add_pull_args(self, opt):
		pass
	
	def add_push_args(self, opt):
		opt.add_argument('-l', '--ubuntu-language', metavar='language', dest='ubuntupaste.lang',
						 help='Language for highlight.')
	
	def push_content(self, content):
		logger.debug('call: ubuntupaste.push_content')
		conf = config.getConfig()
		post_target	= 'http://paste.ubuntu.com/'
		logger.debug('post target: ' + post_target)
		poster		= conf.get('ubuntupaste.user', getpass.getuser())
		logger.debug('poster: ' + poster)
		# Get Filename for highlight.
		filename	= conf.get('push.src', default=config.Raise).name
		lang		= conf.get('ubuntupaste.lang', _get_language(filename))
		logger.debug('highlight: ' + lang)
		post_data	= {
			'poster'	: poster,
			'syntax'	: lang,
			'content'	: content,
		}
		try:
			resp = requests.post(post_target, data=post_data, allow_redirects=False)
		except requests.exceptions.RequestException as e:
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
			return 'ubuntu://' + paste_id
			
		raise exception.ServerException('Server responsed with unknown status %d %s' % (resp.status_code, resp.reason))
		
	
	def pull_content(self, _uri):
		logger.debug('call: ubuntupaste.pull_content')
		res = uri.parse(_uri) # Always ok, no need to check!
		# Paste ID
		pid = res.path
		logger.debug('path: ' + pid)
		for ch in pid:
			if not ch.isdigit():
				raise exception.InvalidURI('UbuntuPaste should only contains digits!')
			
		if pid != str(int(pid)):
			raise exception.InvalidURI('No leading zero allowed.')
		
		url = 'http://paste.ubuntu.com/{pid}/'.format(pid=pid)
		
		logger.info('Built URL: ' + url)
		
		# Check if pad exists
		try:
			res = requests.get(url)
		except requests.exceptions.RequestException as e:
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
			start_len, end_len	= len(start_flag), len(end_flag)
			start_pos	= res.content.find(start_flag)
			logger.debug('start_pos: %d' % start_pos)
			if start_pos < 0:
				raise exception.ServerException('Start flag not found!')
			end_pos		= res.content.find(end_flag, start_pos + start_len)
			logger.debug('end_pos: %d' % end_pos)
			if end_pos < 0:
				raise exception.ServerException('End flag not found!')
			content		= res.content[start_pos + start_len : end_pos]
			# Reset prev pos.
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
			logger.debug('content: %d lines, %d bytes' % (content.count('\n') + 1, len(content)))
			return content
			
		
		if res.status_code >= 400 and res.status_code < 500:
			raise exception.NoSuchPad('No such pad: %s. Server responsed with status code %d' % (_uri, res.status_code))
		
		raise exception.ServerException('Server responsed with status code %d' % res.status_code)
		
	
	def fetch_http_link(self, _uri):
		logger.debug('call: ubuntupaste.fetch_http_link: ' + _uri)
		res = uri.parse(_uri) # Always ok, no need to check!
		# Paste ID
		pid = res.path
		logger.debug('path: ' + pid)
		for ch in pid:
			if not ch.isdigit():
				raise exception.InvalidURI('UbuntuPaste should only contains digits!')
			
		if pid != str(int(pid)):
			raise exception.InvalidURI('No leading zero allowed.')
		
		url = 'http://paste.ubuntu.com/{pid}/'.format(pid=pid)
		
		logger.info('Built URL: ' + url)
		
		# Check if pad exists
		try:
			res = requests.head(url)
		except requests.exceptions.RequestException as e:
			logger.info('Exception: ' + e.__class__.__name__)
			logger.warn('Something wrong when communicating with paste.ubuntu.com, assume paste pad exists.')
			return url
		
		logger.debug('HTTP OK.')
		logger.info('Server response: %d %s' % (res.status_code, res.reason))
		
		if res.status_code == 200: # OK
			return url
		
		if res.status_code >= 400 and res.status_code < 500:
			raise exception.NoSuchPad('No such pad: %s. Server responsed with status code %d' % (_uri, res.status_code))
		
		raise exception.ServerException('Server responsed with status code %d' % res.status_code)
		
