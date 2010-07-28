import datetime
from lib import entry
from lib.helpers import *


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


def _dmap(d, *names):
    return [(d.get(n) or '') for n in names]


def get_or_add_company(s, cname):
    userid = 1
    now = datetime.datetime.now()
    cid = selectone(s, 'select id from accounts where name=?', [cname])
    if cname and not cid:
        cid = s.execute('insert into accounts ' +
                        '  (name, access, ' + 
                        '   user_id, created_at, updated_at, deleted_at) ' +
                        ' values ' +
                        '  (?,"Public", ?,?,?,?)',
                        [cname, userid, now, now, None]).lastrowid
    return cid


def update_contact_company(s, id, cname):
    userid = 1
    now = datetime.datetime.now()
    cid = get_or_add_company(s, cname)
    old_cid = selectone(s, 'select account_id from account_contacts ' +
                        '  where contact_id=? and deleted_at is null ' +
                        '  order by id desc',
                        [id])
    if old_cid != cid:
        s.execute('delete from account_contacts where contact_id=?', [id])
        if cid:
            s.execute('insert into account_contacts ' +
                      '  (account_id, contact_id, ' +
                      '   created_at, updated_at, deleted_at) ' +
                      ' values ' +
                      '  (?,?, ?,?,?)', [cid, id, now, now, None])


def add_contact(s, d):
    userid = 1
    now = datetime.datetime.now()
    id = s.execute('insert into contacts ' +
                   '  (first_name, last_name, title, department, ' +
                   '   email, alt_email, phone, mobile, fax, blog, ' +
                   '   born_on, access, ' + 
                   '   user_id, created_at, updated_at, deleted_at) ' +
                   ' values ' +
                   '  (?,?,?,?, ?,?,?,?,?,?, ?,"Public", ?,?,?,?) ',
                   _dmap(d, 'firstname', 'lastname', 'title', 'department',
                         'email', 'email2', 'phone', 'mobile', 'fax',
                         'web', 'birthdate') + [userid,now,now,None]).lastrowid
    update_contact_company(s, id, d.get('company'))
    return id


def update_contact(s, lid, d):
    assert(lid)
    now = datetime.datetime.now()
    kv = {
        'firstname': 'first_name',
        'lastname': 'last_name',
        'title': 'title',
        'department': 'department',
        'email': 'email',
        'email2': 'alt_email',
        'phone': 'phone',
        'mobile': 'mobile',
        'fax': 'fax',
        'web': 'blog',
        'birthdate': 'born_on',
    }
    setk = ['updated_at']
    setv = [now]
    for (dk,sk) in kv.items():
        setk.append(sk)
        setv.append(d.get(dk))
    q = 'update contacts set %s where id=?' % (', '.join('%s=?' % k
                                                         for k in setk))
    s.execute(q, setv + [lid])
    update_contact_company(s, lid, d.get('company'))
