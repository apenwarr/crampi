from lib import options, gitdb

optspec = """
crampi refs [options]
--
d,gitdb=   name of gitdb sqlite3 database file [crampi.sqlite3]
"""

def main(argv):
    o = options.Options('crampi refs', optspec)
    (opt, flags, extra) = o.parse(argv[1:])

    if extra:
        o.fatal('no arguments expected')

    g = gitdb.GitDb(opt.gitdb)
    for r in g.refs():
        print r
