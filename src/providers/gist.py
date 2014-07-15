#!/usr/bin/env python
# -*- encoding: utf-8 -*-
import argparse
import sys

from lib.provider import ProviderBase
from common import exception
from lib import logger, uri, config

_no_validate = lambda _=None : _

_config_entry = {
	# You may add more entries here.
	# Value can be two types : a list or a validator.
	# If value is a list, user provided value should be one of the element in the list.
	# Otherwise, value is validated by call the validator with the value,
	#   if no exception raised, the value is considered good.
	#   if all values are accepted, use _no_validate
	# 'auth'	: ['anonymous', 'basic'],
	'auth'		: ['anonymous', 'basic', 'oauth'],
	'user'		: _no_validate,
	'pass'		: _no_validate,
}

class Gist(ProviderBase):
	_name = 'gist'
	_info = 'Github gist (https://gist.github.com)'
	def __init__(self):
		logger.debug('call: gist.__init__')
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
