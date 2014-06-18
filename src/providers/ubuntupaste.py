from common.provider import ProviderBase
from common import uri, exception
import requests
from requests import exceptions
from lib import logger

class UbuntuPaste(ProviderBase):

	def __init__(self):
		self.register_protocol('ubuntu')
		
	def add_fetch_args(self, opt):
		pass
	
	def add_pull_args(self, opt):
		pass
	
	def add_push_args(self, opt):
		pass
	
	def pull_content(self, _uri):
		logger.debug('ubuntupaste.pull_content')
	
	def fetch_http_link(self, _uri):
		logger.debug('ubuntupaste.fetch_http_link: ' + _uri)
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
		except requests.exceptions.RequestException:
			logger.warn('Something wrong when communicating with paste.ubuntu.com, assume paste pad exists.')
			return url
		
		logger.debug('HTTP OK.')
		logger.info('Server response: %d %s' % (res.status_code, res.reason))
		
		if res.status_code == 200: # OK
			return url
		
		if res.status_code >= 400 and res.status_code < 500:
			raise exception.NoSuchPad('No such pad: %s. Server responsed with status code %d' % (_uri, res.status_code))
		
		raise exception.ServerException('Server responsed with status code %d' % res.status_code)
		
