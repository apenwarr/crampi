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

    g = gitdb.GitDb(opt.gitdb)
    for r,msg in g.commits_for_ref(extra[0]):
        print '%-8d %s' % (r,msg)
