import sqlite3, yaml
from lib import options, gitdb, entry, ffcrm

optspec = """
crampi crm-export [options] crmdb.sqlite3
--
d,gitdb=   name of gitdb sqlite3 database file
b,branch=  name of git branch to use for CRM data
m,merge=   name of git branch to merge from
v,verbose  print names as they are exported
"""

def main(argv):
    o = options.Options('crampi crm-export', optspec)
    (opt, flags, extra) = o.parse(argv[1:])

    if len(extra) != 1:
        o.fatal('exactly one argument expected')
    opt.crmdb = extra[0]

    if not opt.gitdb:
        opt.gitdb = 'gitdb.sqlite3'
    if not opt.branch:
        opt.branch = 'crm-default'

    g = gitdb.GitDb(opt.gitdb)
    s = sqlite3.connect(opt.crmdb)
    el = entry.Entries(ffcrm.entries(s))
    el.uuids_from_commit(g, opt.branch)
    el.assign_missing_uuids(g)
    if opt.verbose:
        for e in sorted(el.entries, key = lambda x: x.uuid):
            print e
    print el.save_commit(g, opt.branch)

    if opt.merge:
        a_id = g.commitid_lastmerge(opt.branch, opt.merge)
        b_id = g.commitid_latest(opt.merge)
        print 'aid=%s bid=%s' % (a_id, b_id)
        a = entry.load_tree_from_commit(g, a_id)
        b = entry.load_tree_from_commit(g, b_id)
        nel = el.clone()
        for (lid,uuid,ed,ad,bd) in entry.merge(el, a, b):
            d = None
            if not ed: # add
                mode = 'A'
                assert(bd)
                lid = ffcrm.add_contact(s, bd)
                e = entry.Entry(lid, uuid, bd)
                el.entries.append(e)
            elif ad and not bd:  # del
                mode = 'D'
                e = el.uuids[uuid]
            elif ad != bd: # modify
                mode = 'M'
                e = el.uuids[uuid]
            else:
                mode = ''
                e = el.uuids[uuid]
            if mode or opt.verbose:
                print '%1s %s' % (mode, e)
        s.commit()
        el.save_commit(g, opt.branch, b_id)
    
    g.flush()
 
