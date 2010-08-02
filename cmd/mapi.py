import datetime, time
from lib import options, cmapi, gitdb, entry, merge
from lib.helpers import *
from lib.cmapitags import *

optspec = """
crampi mapi <folder name>
--
d,gitdb=   name of gitdb sqlite3 database file [gitdb.sqlite3]
b,branch=  name of git branch to use for these files
m,merge=   name of git branch to merge from
v,verbose  print names as they are exported
"""

_mapping = {
    PR_GIVEN_NAME_W: 'firstname',
    PR_SURNAME_W: 'lastname',
    PR_TITLE_W: 'title',
    PR_DEPARTMENT_NAME_W: 'department',
    PR_COMPANY_NAME_W: 'company',
    pr_custom(0x8083): 'email',  # Email1Address in OutlookObjectModel
    pr_custom(0x8093): 'email2', # Email2Address in OOM
    PR_BUSINESS_TELEPHONE_NUMBER_W: 'phone',
    PR_MOBILE_TELEPHONE_NUMBER_W: 'mobile',
    PR_BUSINESS_FAX_NUMBER_W: 'fax',
    PR_BUSINESS_HOME_PAGE_W: 'web',
    PR_BIRTHDAY: 'birthdate',
}
_admapping = {
    PR_BUSINESS_ADDRESS_STREET_W: 'street1',
    PR_BUSINESS_ADDRESS_CITY_W: 'city',
    PR_BUSINESS_ADDRESS_STATE_OR_PROVINCE_W: 'state',
    PR_BUSINESS_ADDRESS_POSTAL_CODE_W: 'zip',
    PR_BUSINESS_ADDRESS_COUNTRY_W: 'country',
    PR_POSTAL_ADDRESS_W: 'fulladdress',
}

_mapping_r = dict((v,k) for k,v in _mapping.items())
_admapping_r = dict((v,k) for k,v in _admapping.items())


def entries(f):
    keys = [PR_ENTRYID] + _mapping.keys() + _admapping.keys()
    for m in f.messages().iter(*keys):
        d = {}
        ad = {}
        for k,kk in _mapping.items():
            v = m.get(k)
            if type(v).__name__ in ['PyTime', 'time']:
                v = unicode(v)
            d[kk] = v
        for k,kk in _admapping.items():
            ad[kk] = m.get(k)
        if filter(None, ad.values()):
            ad['type'] = 'Business'
            d['addresses'] = [ad]
        yield entry.Entry(m.get(PR_ENTRYID), None, d)


_v = 5
def add_contact(f, d):
    log('--\nadd_contact: %r\n' % d)
    global _v
    _v += 1
    return _v


def update_contact(f, lid, d, changes):
    log('--\nupdate_contact %r: %r\n' % (lid, changes))
    msg = f.message(lid, repr(lid))
    # note: the above should always succeed, since merge.run() has already
    # made sure of what's a delete vs. modify vs. add.
    for k,v in changes.items():
        if k == 'addresses':
            continue
        pr = _mapping_r.get(k)
        print 'updating: %r' % ((pr,k,v),)
        if pr:
            msg.setprops((pr, v))
    adlist = changes.get('addresses')
    if adlist:
        for k,v in adlist[0].items():
            pr = _admapping_r.get(k)
            print 'ad_updating: %r' % ((pr,k,v),)
            if pr:
                msg.setprops((pr, v))
    msg.save()


def main(argv):
    o = options.Options('crampi mapi', optspec)
    (opt, flags, extra) = o.parse(argv[1:])

    if len(extra) != 1:
       o.fatal('you must provide exactly one folder name')
    fname = extra[0]

    if not opt.branch:
        o.fatal('you must specify the -b option')

    g = gitdb.GitDb(opt.gitdb)
    sess = cmapi.Session()
    f = sess.recursive_find(fname)
    el = entry.Entries(entries(f))
    el.uuids_from_commit(g, opt.branch)
    el.assign_missing_uuids(g)
    if opt.verbose:
        for e in sorted(el.entries, key = lambda x: x.uuid):
            print e
    print el.save_commit(g, opt.branch,
                         msg='exported from mapi %r on %s'
                            % (fname, time.asctime()))
    
    if opt.merge:
        merge.run(g, el, opt.branch, opt.merge, opt.verbose,
                  add_contact = lambda d: add_contact(f, d),
                  update_contact = lambda lid, d, changes: 
                      update_contact(f, lid, d, changes),
                  commit_contacts = lambda: None)
    
    g.flush()
    
