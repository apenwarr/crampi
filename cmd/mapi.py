import datetime, time
from lib import options, cmapi, gitdb, entry, merge
from lib.helpers import *
from lib.cmapitags import *

optspec = """
crampi mapi <folder name>
--
d,gitdb=   name of gitdb sqlite3 database file [crampi.sqlite3]
b,branch=  name of git branch to use for these files
m,merge=   name of git branch to merge from
v,verbose  print names as they are exported
"""

_email_prop = pr_custom(0x8083)   # Email1Address in OutlookObjectModel
_email2_prop = pr_custom(0x8093)  # Email2Address in OOM
_email_disp_prop = pr_custom(0x8084)   # Email1DisplayName in OOM
_email2_disp_prop = pr_custom(0x8094)  # Email2DisplayName in OOM
_fileas_prop = pr_custom(0x8005)  # FileAs in OOM

_mapping = {
    PR_GIVEN_NAME_W: 'firstname',
    PR_SURNAME_W: 'lastname',
    PR_TITLE_W: 'title',
    PR_DEPARTMENT_NAME_W: 'department',
    PR_COMPANY_NAME_W: 'company',
    _email_prop: 'email',
    _email2_prop: 'email2',
    PR_HOME_TELEPHONE_NUMBER_W: 'homephone',
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

def _dnullify(d):
    for k in d.keys():
        if not d[k]:
            del d[k]
    return d


def entries(f):
    keys = ([PR_ENTRYID, PR_LONGTERM_ENTRYID_FROM_TABLE] +
            _mapping.keys() + _admapping.keys())
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
            d['addr_biz'] = _dnullify(ad)
        yield entry.Entry(m.get(PR_LONGTERM_ENTRYID_FROM_TABLE) 
                          or m.get(PR_ENTRYID),
                          None, _dnullify(d))


def _displayname(last, first, company):
    if last and first:
        return '%s, %s' % (last, first)
    elif last:
        return last
    elif first:
        return first
    else:
        return company


def _setprops(msg, d):
    for k,v in d.items():
        if k == 'addr_biz':
            continue
        pr = _mapping_r.get(k)
        #print 'updating: %r' % ((pr,k,v),)
        if pr:
            msg.setprops((pr, v))
        if k == 'email':
            msg.setprops((_email_disp_prop, v))
        elif k == 'email2':
            msg.setprops((_email2_disp_prop, v))
    for k,v in d.get('addr_biz', {}).items():
        pr = _admapping_r.get(k)
        #print 'ad_updating: %r' % ((pr,k,v),)
        if pr:
            msg.setprops((pr, v))


def add_contact(f, d):
    #log('--\nadd_contact: %r\n' % d)
    msg = f.newmessage()
    displayname = _displayname(d.get('lastname'), d.get('firstname'),
                               d.get('company'))
    msg.setprops((PR_MESSAGE_CLASS, 'IPM.Contact'))
    msg.setprops((PR_DISPLAY_NAME_W, displayname),
                 (_fileas_prop, displayname))
    _setprops(msg, d)
    msg.save()
    lid = msg.get(PR_LONGTERM_ENTRYID_FROM_TABLE) or msg[PR_ENTRYID]
    assert(lid)
    log('created contact: %r\n' % (str(lid).encode('hex'),))
    return lid


def update_contact(f, lid, d, changes):
    #log('--\nupdate_contact %r: %r\n' % (lid, changes))
    msg = f.message(lid, repr(lid))
    # note: the above should always succeed, since merge.run() has already
    # made sure of what's a delete vs. modify vs. add.
    displayname = _displayname(d.get('lastname'), d.get('firstname'),
                               d.get('company'))
    msg.setprops((PR_DISPLAY_NAME_W, displayname),
                 (_fileas_prop, displayname))
    _setprops(msg, changes)
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
            log('%s\n' % e)
    print el.save_commit(g, opt.branch,
                         msg='exported from mapi %r on %s'
                            % (fname, time.asctime()))
    
    if opt.merge:
        def do_load(el):
            el2 = entry.Entries(entries(f))
            el2.uuids_from_entrylist(el)
            el2.assert_all_uuids()
            return el2
            
        print merge.run(g, el, opt.branch, opt.merge, opt.verbose,
                        add_contact = lambda d: add_contact(f, d),
                        update_contact = lambda lid, d, changes: 
                             update_contact(f, lid, d, changes),
                        commit_contacts = lambda: None,
                        reload_entrylist = do_load)
    
    g.flush()
    
