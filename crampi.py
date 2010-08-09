#!/usr/bin/env python
import sys, os, getopt
from lib import options
from lib.helpers import *

optspec = """
crampi <command> [options...]
"""

def usage(msg = ''):
    log('usage: crampi <command> [options...]\n' +
        '\n' +
        'Available commands:\n')
    for n in sorted(os.listdir('cmd')):
        if n.endswith('.py') and not n[0] in ['_', '.']:
            log('  %s\n' % n[:-3])
    sys.exit(99)


o = options.Options('crampi', optspec, optfunc=getopt.getopt)
o.usage = usage
(opt, flags, extra) = o.parse(sys.argv[1:])

if not extra:
    o.fatal('you must provide a command name')

cmd = extra[0]
def parent_dir(fn):
    return os.path.split(os.path.abspath(fn))[0]
exedirs = [parent_dir(sys.argv[0]),
           parent_dir(os.path.realpath(sys.argv[0]))]
sys.path[:0] = exedirs

def exedirs_contains(cmd):
    for dir in exedirs:
        if os.path.exists('%s/cmd/%s.py' % (dir, cmd)):
            return dir

if not exedirs_contains(cmd):
    o.fatal('no subcommand named %r' % cmd)
m = __import__('cmd.%s' % cmd, fromlist=['main'])
m.main(argv = extra)
