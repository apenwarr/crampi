import sqlite3, yaml
from lib import options, gitdb, entry

optspec = """
crampi crm-export [-d db.sqlite3] crmdb.sqlite3
--
d,gitdb=   name of gitdb sqlite3 database file
"""

def entries(s):
    q = ('select id, first_name, last_name, title, department, ' +
         '    email, alt_email, phone, mobile, fax, blog, born_on, ' +
         '    deleted_at ' + 
         ' from contacts ' +
         ' where access = "Public" and deleted_at is null')
    aq = ('select street1, street2, city, state, zipcode, country, ' +
          '   full_address, address_type ' +
          ' from addresses ' +
          ' where addressable_id=? and addressable_type="Contact" ' +
          '    and deleted_at is null ' +
          ' order by id')
    cq = ('select accounts.name from account_contacts ' +
          ' join accounts on accounts.id=account_id ' +
          ' where contact_id=? and account_contacts.deleted_at is null ' +
          '    and accounts.deleted_at is null ' +
          ' order by account_contacts.id' +
          ' limit 1')
    for (lid, fn, ln, title, dept,
         email, email2, phone, mobile, fax, web, birthdate,
         deleted) in s.execute(q):
        d = dict(firstname=fn, lastname=ln, title=title,
                 department=dept, email=email, email2=email2, phone=phone,
                 mobile=mobile, fax=fax, web=web, birthdate=birthdate)
        d['addresses'] = []
        d['company'] = None
        for (street1, street2, city, state, zip, country,
             fullad, adtype) in s.execute(aq, [lid]):
            d['addresses'].append(dict(street1=street1,
                                       street2=street2,
                                       city=city, state=state,
                                       zip=zip, country=country,
                                       fulladdress=fullad,
                                       type=adtype))
        for (cname,) in s.execute(cq, [lid]):
            d['company'] = cname
        yield entry.Entry(lid, None, d)


def main(argv):
    o = options.Options('crampi crm-export', optspec)
    (opt, flags, extra) = o.parse(argv[1:])

    if len(extra) != 1:
        o.fatal('exactly one argument expected')
    opt.crmdb = extra[0]

    if not opt.gitdb:
        opt.gitdb = 'gitdb.sqlite3'

    s = sqlite3.connect(opt.crmdb)
    el = entry.Entries(entries(s))
    #for e in entries(s):
    #    print yaml.safe_dump((e.lid,e.d), default_flow_style=False)
    
    g = gitdb.GitDb(opt.gitdb)
    el.uuids_from_commit(g, opt.crmdb)
    el.assign_missing_uuids(g)
    t = el.save_tree(g)
    print t
    el2 = entry.load_tree(g, t)
    t2 = el.save_tree(g)
    assert(t == t2)
    print el.save_commit(g, opt.crmdb)
    #print yaml.safe_dump_all(entries(), width=40)
    #print len(list(entries()))
    #list(entries())
    g.flush()
