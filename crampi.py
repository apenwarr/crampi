#!/usr/bin/env cxpython
import sys
from pythoncom import IID_IUnknown
from win32com.mapi import mapi, mapitags
from win32com.mapi.mapitags import *

def log(s):
    sys.stdout.flush()
    sys.stderr.write(s)
    sys.stderr.flush()

propnames = {}
for (_name,_num) in mapitags.__dict__.iteritems():
    if _name.startswith('PR_'):
        propnames[_num] = _name


def pr_to_name(num):
    return propnames.get(num, num)

def binclean(s):
    if not isinstance(s, basestring):
        return s
    def clean(c):
        return (ord(c) >= 32 and ord(c) < 127) and c or '.'
    return ''.join(clean(c) for c in s)


class Mapi:
    def __init__(self, handle):
        self.h = handle

    def _open(self, entryid):
        return self.h.OpenEntry(entryid, None, mapi.MAPI_BEST_ACCESS)

    def _find(self, table, name):
        for (eid, ename) in table.iter(PR_ENTRYID, PR_DISPLAY_NAME_W):
            if ename == name or eid == name:
                return eid


class BaseProps:
    def __init__(self, pclass, proplist):
        self.proporder = []
        self.propcache = {}
        self.pclass = pclass
        self.importprops(proplist)

    def __getitem__(self, propid):
        if not propid in self.propcache:
            pidstr = mapitags.__dict__.get(propid)
            self.loadprops(pidstr or propid)
        return self.propcache[propid]

    def __repr__(self):
        return '%s {\n  %s\n}' \
            % (self.pclass.__name__,
               ',\n  '.join('%s: %r' % (pr_to_name(k), binclean(v))
                            for k,v in self.iteritems()))

    def __iter__(self):
        return self.itervalues()

    def iterkeys(self):
        for k in self.proporder:
            yield k

    def itervalues(self):
        for k in self.proporder:
            yield self.propcache[k]

    def iteritems(self):
        for k in self.proporder:
            yield k, self.propcache[k]

    def keys(self):
        return list(self.iterkeys())

    def values(self):
        return list(self.itervalues())

    def items(self):
        return list(self.iteritems())

    def loadprops(self, *propids):
        pass

    def _addprop(self, k, v):
        self.propcache[k] = v
        if not k in self.proporder:
            self.proporder.append(k)

    def importprops(self, proplist):
        for k,v in proplist:
            self._addprop(k,v)



class Props(Mapi,BaseProps):
    def __init__(self, handle):
        Mapi.__init__(self, handle)
        BaseProps.__init__(self, self.__class__, [])
        self.propcache = {}

    def loadprops(self, *propids):
        ret, props = self.h.GetProps(propids)
        for k,v in props:
            self.propcache[k] = v


class Message(Props):
    pass


class Table(Mapi):
    def __init__(self, pclass, handle):
        Mapi.__init__(self, handle)
        self.pclass = pclass
        
    def iter(self, *cols):
        self.h.SeekRow(mapi.BOOKMARK_BEGINNING, 0)
        if not cols:
            cols = self.h.QueryColumns(mapi.TBL_ALL_COLUMNS)
        self.h.SetColumns(cols, 0)
        while 1:
            rows = self.h.QueryRows(1024, 0)
            for row in rows:
                yield BaseProps(self.pclass, row)
            if len(rows) < 1024:
                break

    def __iter__(self):
        return self.iter()


class Container(Props):
    def children(self):
        return Table(Container, self.h.GetHierarchyTable(mapi.MAPI_UNICODE))

    def messages(self):
        return Table(Message, self.h.GetContentsTable(mapi.MAPI_UNICODE))

    def child(self, entryid):
        return Container(self._open(entryid))

    def message(self, entryid):
        return Message(self._open(entryid))


class Store(Props):
    def child(self, entryid):
        return Container(self._open(entryid))

    def root(self):
        return self.child(self[PR_IPM_SUBTREE_ENTRYID])


class Session(Mapi):
    def __init__(self, hwnd = 0, profile = None, password = None):
        mapi.MAPIInitialize((mapi.MAPI_INIT_VERSION,0))
        flags = mapi.MAPI_EXTENDED
        if not profile:
            flags |= mapi.MAPI_USE_DEFAULT
        h = mapi.MAPILogonEx(hwnd, profile or '', password or '', flags)
        Mapi.__init__(self, h)

    def stores(self):
        return Table(Store, self.h.GetMsgStoresTable(0))

    def store(self, entryid):
        return Store(self.h.OpenMsgStore(0, entryid, None,
                        mapi.MDB_NO_DIALOG | mapi.MAPI_BEST_ACCESS))



sess = Session()
stores = sess.stores()
for row in stores.iter(PR_ENTRYID, PR_DISPLAY_NAME_W, PR_DEFAULT_STORE):
    print row
    print '---'
for (eid,name,default) in stores.iter(PR_ENTRYID, PR_DISPLAY_NAME_W,
                                      PR_DEFAULT_STORE):
    if not default:
        break

# unpack the row and open the message store
store = sess.store(eid)
root = store.root()

def show_cont(indent, c):
    for eid,name,subf in c.children().iter(PR_ENTRYID, PR_DISPLAY_NAME_W,
                                           PR_SUBFOLDERS):
        print '%s%s' % (indent, name)
        if subf:
            show_cont(indent+'    ', c.child(eid))

show_cont('', root)
