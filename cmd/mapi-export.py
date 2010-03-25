from lib import options, cmapi, gitdb, entry
from lib.cmapitags import *

optspec = """
crampi mapi-export <folder name>
--
d,gitdb=   name of gitdb sqlite3 database file
b,branch=  name of git branch to use for these files
v,verbose  print names as they are exported
"""

_mapping = {
    PR_GIVEN_NAME_W: 'firstname',
    PR_SURNAME_W: 'lastname',
    PR_TITLE_W: 'title',
    PR_DEPARTMENT_NAME_W: 'department',
    # 0x81ae Email1Address: 'email',
    # 0x81b3 Email2Address: 'email2',
    PR_BUSINESS_TELEPHONE_NUMBER_W: 'phone',
    PR_MOBILE_TELEPHONE_NUMBER_W: 'mobile',
    PR_BUSINESS_FAX_NUMBER_W: 'fax',
    PR_BUSINESS_HOME_PAGE_W: 'blog',
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


def entries(f):
    keys = [PR_ENTRYID] + _mapping.keys() + _admapping.keys()
    for m in f.messages().iter(*keys):
        d = {}
        ad = {}
        for k,kk in _mapping.items():
            d[kk] = m.get(k)
        for k,kk in _admapping.items():
            ad[kk] = m.get(kk)
        if filter(None, ad.values()):
            ad['type'] = 'Business'
            d['addresses'] = [ad]
        yield entry.Entry(m.get(PR_ENTRYID), None, d)


def main(argv):
    o = options.Options('crampi mapi-export', optspec)
    (opt, flags, extra) = o.parse(argv[1:])

    if len(extra) != 1:
       o.fatal('you must provide exactly one folder name')
    fname = extra[0]

    if not opt.gitdb:
        opt.gitdb = 'gitdb.sqlite3'
    if not opt.branch:
        opt.branch = 'mapi-default'

    g = gitdb.GitDb(opt.gitdb)
    sess = cmapi.Session()
    f = sess.recursive_find(fname)
    el = entry.Entries(entries(f))
    el.uuids_from_commit(g, opt.branch)
    el.assign_missing_uuids(g)
    if opt.verbose:
        for e in sorted(el.entries, key = lambda x: x.uuid):
            print e
    print el.save_commit(g, opt.branch)
    g.flush()
    
