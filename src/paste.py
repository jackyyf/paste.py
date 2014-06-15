_version	= '0.0.1 Alpha'

import sys
import os
import argparse
from lib import logger
import ConfigParser

# Change default encoding to UTF-8

reload(sys)
sys.setdefaultencoding('UTF-8')
del sys.setdefaultencoding

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
	opt_log.add_argument('--simple-log', action='store_const', dest='log.mode', const='{message}',
						 default=None, help='Output just simple message without timestamp, log level etc.')
	opt_log.add_argument('--no-color', action='store_const', dest='log.colorize', const=False,
						 default=True, help='Disable colorful output. Note: colorful is always false if output file is not a terminal.')
	opt_action = parser.add_subparsers(title='Actions', help='Help message', metavar='action')
	action_push = opt_action.add_parser('push', help='Push a paste to remote paste pad')
	action_pull = opt_action.add_parser('pull', help='Pull a paste from remote paste pad')
	args = parser.parse_args()
	print args._get_args()

if __name__ == '__main__':
	run()