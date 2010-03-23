#!/usr/bin/env cxpython
import sys, re
from lib import options

optspec = """
crampi [options] [folders...]
--
folders   list subfolders of the given mapi folders
list      list the messages in the given mapi folders
crmdb=    use the given fat_free_crm sqlite3 database file
gitdb=    use the given gitdb database for storing history
crm-export export from fat_free_crm to gitdb
"""
o = options.Options('crampi', optspec)
(opt, flags, extra) = o.parse(sys.argv[1:])

if not opt.gitdb:
    opt.gitdb = 'gitdb.sqlite3'

if not (opt.folders or opt.list or opt.crm_export):
    o.fatal('must provide --folders, --list, or --crm-export')

def mapi_init():
    from lib import cmapi
    global sess, stores
    sess = cmapi.Session()
    stores = [sess.store(row[PR_ENTRYID])
              for row in sess.stores().iter(PR_ENTRYID)]

    

if opt.folders:
    from lib.cmapitags import *
    mapi_init()
    def show_cont(indent, c):
        for eid,name,subf in c.children().iter(PR_ENTRYID, PR_DISPLAY_NAME_W,
                                               PR_SUBFOLDERS):
            print '%s%s' % (indent, name)
            if subf:
                show_cont(indent+'    ', c.child(eid))
    if not extra:
        show_cont('', sess)
    else:
        for name in extra:
            show_cont('', sess.recursive_find(name))

if opt.list:
    from lib.cmapitags import *
    mapi_init()
    if not extra:
        o.fatal('must provide a folder name to list')
    for name in extra:
        f = sess.recursive_find(name)
        for m in f.messages().iter(PR_NORMALIZED_SUBJECT, PR_TITLE_W):
            print repr(m.get(PR_NORMALIZED_SUBJECT+1000, m))

if opt.crm_export:
    if not opt.crmdb:
        o.fatal('must provide a value for --crmdb')
    import sqlite3, yaml
    s = sqlite3.connect(opt.crmdb)
    def entries():
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
        for (cid, fn, ln, title, dept,
             email, email2, phone, mobile, fax, web, birthdate,
             deleted) in s.execute(q):
            d = dict(firstname=fn, lastname=ln, title=title,
                     department=dept, email=email, email2=email2, phone=phone,
                     mobile=mobile, fax=fax, web=web, birthdate=birthdate)
            d['addresses'] = []
            d['company'] = None
            for (street1, street2, city, state, zip, country,
                 fullad, adtype) in s.execute(aq, [cid]):
                     d['addresses'].append(dict(street1=street1,
                                                street2=street2,
                                                city=city, state=state,
                                                zip=zip, country=country,
                                                fulladdress=fullad,
                                                type=adtype))
            for (cname,) in s.execute(cq, [cid]):
                d['company'] = cname
            yield cid,d
    for (lid,e) in entries():
        print yaml.safe_dump((lid,e), default_flow_style=False)
    #print yaml.safe_dump_all(entries(), width=40)
    #print len(list(entries()))
    #list(entries())
    
    
