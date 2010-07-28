from lib import options, gitdb

optspec = """
crampi log [refname]
--
d,gitdb=   name of gitdb sqlite3 database file [gitdb.sqlite3]
"""

def main(argv):
    o = options.Options('crampi log', optspec)
    (opt, flags, extra) = o.parse(argv[1:])

    if len(extra) > 1:
        o.fatal('at most one refname expected; use "crampi refs" for a list')

    refname = extra and extra[0] or None

    g = gitdb.GitDb(opt.gitdb)
    if refname and not g.commitid_latest(refname):
        o.fatal('invalid refname; use "crampi refs" for a list')

    for r,ref,msg in g.commits(refname=refname):
        print '%-6d %-10s %s' % (r,ref,msg)
