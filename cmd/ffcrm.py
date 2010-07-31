import os, sqlite3, time
from lib import options, gitdb, entry, ffcrm, merge

optspec = """
crampi ffcrm [options] crmdb.sqlite3
--
d,gitdb=   name of gitdb sqlite3 database file [gitdb.sqlite3]
b,branch=  name of git branch to use for CRM data
m,merge=   name of git branch to merge from
v,verbose  print names as they are exported
"""

def main(argv):
    o = options.Options('crampi ffcrm', optspec)
    (opt, flags, extra) = o.parse(argv[1:])

    if len(extra) != 1:
        o.fatal('exactly one argument expected')
    opt.crmdb = extra[0]

    if not opt.branch:
        o.fatal('you must specify the -b option')
    if not os.path.exists(opt.crmdb):
        o.fatal('crmdb %r does not exist' % opt.crmdb)
    if opt.merge == opt.branch:
        o.fatal('--merge parameter %r must differ from branch %r'
                % (opt.merge, opt.branch))

    g = gitdb.GitDb(opt.gitdb)
    s = sqlite3.connect(opt.crmdb)
    el = entry.Entries(ffcrm.entries(s))
    el.uuids_from_commit(g, opt.branch)
    el.assign_missing_uuids(g)
    if opt.verbose:
        for e in sorted(el.entries, key = lambda x: x.uuid):
            print e
    print el.save_commit(g, opt.branch, 'exported from ffcrm %r' % opt.crmdb)

    if opt.merge:
        merge.run(g, el, opt.branch, opt.merge, opt.verbose,
                  add_contact = lambda d: ffcrm.add_contact(s, d),
                  update_contact = lambda lid, d: 
                        ffcrm.update_contact(s, lid, d),
                  commit_contacts = lambda: s.commit())
    
    g.flush()
