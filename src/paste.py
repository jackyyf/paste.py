_version	= '0.0.1'

import sys
import os
import argparse

from lib import logger, config, uri
from lib.provider import ProviderBase, getProvider

# Change default encoding to UTF-8

reload(sys)
sys.setdefaultencoding('UTF-8')
del sys.setdefaultencoding

sys.path = [os.path.abspath('.')] + sys.path

class _Smart_formatter(argparse.HelpFormatter):
    def _split_lines(self, text, width):
        # this is the RawTextHelpFormatter._split_lines
        if '\n' in text:
            return text.splitlines()
        return argparse.HelpFormatter._split_lines(self, text, width)

def run():
	parser = argparse.ArgumentParser(prog='paste.py', description='Push to or pull from paste pads!',
                                     conflict_handler='resolve', add_help=False,
                                     formatter_class=_Smart_formatter)
	opt_common = parser.add_argument_group('Common Options')
	opt_common.add_argument('-h', '--help', action='help',
                            help='Print this help message and exit.\n'
                            'Use `paste.py provider -h` for specific information.')
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
	opt_action = parser.add_subparsers(title='Paste pads', help='introduction', metavar='provider', dest='provider')
	__import__('providers', globals(), locals())
	for provider in ProviderBase.__subclasses__():
		ins = provider()
		opt_ins = opt_action.add_parser(ins._name, help=ins._info, conflict_handler='resolve')
		ins.add_args(opt_ins)
	args = parser.parse_args()
	conf = config.getConfig()
	for arg in args._get_kwargs():
		conf.set(arg[0], arg[1])
	logger.init(colorize=conf.getboolean('log.colorize'), level=conf.getint('log.level'), log_format=conf.get('log.format'))
	getProvider(conf.get('provider')).run()

if __name__ == '__main__':
	run()
