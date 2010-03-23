#!/usr/bin/env python
import sys, os, getopt
from lib import options
from lib.helpers import *

optspec = """
crampi <command> [options...]
"""

def usage():
    log('usage: crampi <command> [options...]\n' +
        '\n' +
        'Available commands:\n')
    for n in os.listdir('cmd'):
        if n.endswith('.py') and not n[0] in ['_', '.']:
            log('  %s\n' % n[:-3])
    sys.exit(99)


o = options.Options('crampi', optspec, optfunc=getopt.getopt)
o.usage = usage
(opt, flags, extra) = o.parse(sys.argv[1:])

if not extra:
    o.fatal('you must provide a command name')

m = __import__('cmd.%s' % extra[0], fromlist=['main'])
m.main(argv = extra)
