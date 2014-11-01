paste.py
========

Send & fetch pastes with command line!  
No more ftp, sftp, scp or something else. Just push at server, pull at 
client, everything is done!  
And also, share config file, source code, or any other text files to 
friend is also very easy with paste.py!

Highlight Support
----------------

By default, content are pushed with no syntax highlight(syntax: plain 
text), but you may specify or get from suffix of filename :)

Supported Pastepad
------------------

ubuntupaste:	http://paste.ubuntu.com/ (Not Blocked in China 
Mainland)  
pastebin:		http://pastebin.com/ (stub)  
pastie:			http://pastie.org/ (stub)  
gist:			https://gist.github.com/ (Login/API Key Required)

Your favorite pastepad is not listed? Open an issue, and I'll add it :)

Dependency
----------

python 2.x:	    tested with 2.7.8  
colorama:       tested with 0.3.1  
automodinit:    tested with 0.13  
argparse:		tested with 1.2.1 (for python version < 2.7)

### provider specific

#### ubuntupaste

requests:		tested with 2.4.3

#### gist

requests:		tested with 2.4.3

Contribute
----------

You may buy me a beer if you think this project is useful to you :)  
Paypal: [![Buy me a beer!](https://www.paypal.com/en_US/i/btn/btn_donate_LG.gif)]
(https://www.paypal.com/cgi-bin/webscr?cmd=_s-xclick&hosted_button_id=67RKC8NB5RQNE)  
Alipay: 0.0@eve.moe  

Or you may want to add a provider, for everybody to use :)
