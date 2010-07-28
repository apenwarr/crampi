from lib import options, gitdb

optspec = """
crampi log <refname>
--
d,gitdb=   name of gitdb sqlite3 database file [gitdb.sqlite3]
"""

def main(argv):
    o = options.Options('crampi log', optspec)
    (opt, flags, extra) = o.parse(argv[1:])

    if len(extra) != 1:
        o.fatal('exactly one refname expected; use "crampi refs" for a list')
    refname = extra[0]

    g = gitdb.GitDb(opt.gitdb)
    if not g.commitid_latest(refname):
        o.fatal('invalid refname; use "crampi refs" for a list')

    for r,msg in g.commits_for_ref(refname):
        print '%-8d %s' % (r,msg)
