_version	= '0.0.1 Alpha'

import sys
import os
import argparse

from lib import logger, config, uri
from lib.provider import ProviderBase, getHandlerClass

# Change default encoding to UTF-8

reload(sys)
sys.setdefaultencoding('UTF-8')
del sys.setdefaultencoding

sys.path = [os.path.abspath('.')] + sys.path

def run():
	parser = argparse.ArgumentParser(prog='paste.py', description='Push to or pull from paste pads!', conflict_handler='resolve')
	opt_common = parser.add_argument_group('Common Options')
	opt_common.add_argument('-h', '--help', action='help', help='Print this help message and exit.')
	opt_common.add_argument('-V', '--version', action='version', version='%(prog)s ' + _version)
	opt_log = parser.add_argument_group('Logging Options')
	opt_log.add_argument('--verbose', '-v', action='store_const', dest='log.level', const=logger.Level.INFO,
						 default=logger.Level.WARN, help='Enable verbose output.')
	opt_log.add_argument('--debug', '-g', action='store_const', dest='log.level', const=logger.Level.DEBUG,
						 help='Enable debug output. (VERY VERBOSE!)')
	opt_log.add_argument('--quiet', '-q', action='store_const', dest='log.level', const=logger.Level.ERROR,
						 help='Just be quiet, output only error message.')
	opt_log.add_argument('--simple-log', action='store_const', dest='log.format', const='{message}',
						 default=None, help='Output just simple message without timestamp, log level etc.')
	opt_log.add_argument('--no-color', action='store_const', dest='log.colorize', const=False,
						 default=True, help='Disable colorful output. Note: colorful is always false if output file is not a terminal.')
	opt_action = parser.add_subparsers(title='Actions', help='===== Help message =====', metavar='action', dest='paste.action')
	action_push = opt_action.add_parser('push', help='Push a paste to remote paste pad', conflict_handler='resolve')
	push_common = action_push.add_argument_group('Common Options')
	push_common.add_argument('-h', '--help', action='help', help='Print this help message and exit.')
	push_args = action_push.add_argument_group('Arguments')
	push_args.add_argument(metavar='pastepad', dest='push.dest', help='Pastepad you want to paste to.')
	push_args.add_argument(metavar='file', nargs='?', dest='push.src', help='Local file you want to paste. Use - or ignore it to read from stdin.',
						   type=argparse.FileType('r'), default='-')
	action_pull = opt_action.add_parser('pull', help='Pull a paste from remote paste pad', conflict_handler='resolve')
	pull_common = action_pull.add_argument_group('Common Options')
	pull_common.add_argument('-h', '--help', action='help', help='Print this help message and exit.')
	pull_args = action_pull.add_argument_group('Arguments')
	pull_args.add_argument(metavar='uri', dest='pull.src', help='Pastepad you want to fetch from.')
	pull_args.add_argument(metavar='file', nargs='?', dest='pull.dest', help='Local file you want to store. Use - or ignore it to write to stdout.',
						   type=argparse.FileType('w'), default='-')
	action_fetch = opt_action.add_parser('fetch', help='Fetch http link from paste uri', conflict_handler='resolve')
	fetch_args = action_fetch.add_argument_group('Arguments')
	fetch_args.add_argument(metavar='uri', dest='pull.dest', help='Pastepad uri to resolve.')
	fetch_common = action_fetch.add_argument_group('Common Options')
	fetch_common.add_argument('-h', '--help', action='help', help='Print this help message and exit.')
	__import__('providers', globals(), locals())
	for provider in ProviderBase.__subclasses__():
		ins = provider()
		ins.add_push_args(action_push.add_argument_group('Options for ' + provider.__name__))
		ins.add_pull_args(action_pull.add_argument_group('Options for ' + provider.__name__))
		ins.add_fetch_args(action_fetch.add_argument_group('Options for ' + provider.__name__))
	args = parser.parse_args()
	conf = config.getConfig()
	for arg in args._get_kwargs():
		conf.set(arg[0], arg[1])
	logger.init(colorize=conf.getboolean('log.colorize'), level=conf.getint('log.level'), log_format=conf.get('log.format'))
	actions[conf.get('paste.action')]()
	
def push():
	logger.debug('call: push')
	conf = config.getConfig()
	src_fd = conf.get('push.src', default=config.Raise)
	logger.debug('src_fd: ' + str(src_fd))
	name	= conf.get('push.dest')
	logger.debug('push.dest: ' + name)
	provider = getHandlerClass(name)
	logger.debug('provider:' + provider.__class__.__name__)
	if src_fd.name == '<stdin>':
		logger.info('paste source: read from stdin')
		print 'Input should be ended with EOF(Ctrl-D at a newline)'
		print 'Or Ctrl-C to terminate the program.'
	try:
		content = src_fd.read()
		logger.info('content: %d lines, %d bytes' % (content.count('\n') + 1, len(content)))
	except KeyboardInterrupt:
		print 'SIGINT(Ctrl-C) detected, exiting...'
		sys.exit(1)
		
	_uri = provider.push_content(content)
	print 'http url:' + provider.fetch_http_link(_uri)
	print 'paste.py uri: ' + _uri
	
def pull():
	logger.debug('call: pull')
	conf = config.getConfig()
	dest_fd = conf.get('pull.dest', default=config.Raise)
	logger.debug('dest_fd: ' + str(dest_fd))
	uri	= conf.get('pull.src')
	logger.debug('pull.src: ' + uri)
	provider = getHandlerClass(uri)
	logger.debug('provider:' + provider.__class__.__name__)
		
	content = provider.pull_content(uri)
	
	dest_fd.write(content)
	
	logger.info('Write to fd ok.')
	
actions = {
	'push'	: push,
	'pull'	: pull,
}
		

if __name__ == '__main__':
	run()
