import fnmatch, time
from win32com.mapi import mapi, mapitags
from win32com.mapi.mapitags import *


class OpenFailed(Exception):
    pass


propnames = {}
for (_name,_num) in mapitags.__dict__.iteritems():
    if _name.startswith('PR_'):
        propnames[_num] = _name


def pr_to_name(num):
    return propnames.get(num, num)


def _lookup_custom_props(handle, l):
    for i in l:
        if isinstance(i, int):
            yield i
        else:
            yield i(handle)


def _lookup_custom_props_tuple(handle, l):
    l1 = [k for k,v in l]
    l2 = [v for k,v in l]
    for k,v in zip(_lookup_custom_props(handle, l1), l2):
        if v and (PROP_TYPE(k) in (PT_APPTIME,PT_SYSTIME)):
            v = time.strptime(v, '%m/%d/%y %H:%M:%S')
        yield k,v


def binclean(s):
    if not isinstance(s, basestring):
        return s
    def clean(c):
        return (ord(c) >= 32 and ord(c) < 127) and c or '.'
    return ''.join(clean(c) for c in s)


class Mapi:
    def __init__(self, handle):
        self.h = handle

    def _open(self, entryid, nicename):
        try:
            return self.h.OpenEntry(entryid, None, mapi.MAPI_BEST_ACCESS)
        except Exception, e:
            raise OpenFailed("Can't open %s: %r" % (nicename, e))

    def _find(self, table, name):
        for (eid, ename) in table.iter(PR_ENTRYID, PR_DISPLAY_NAME_W):
            if eid == name or fnmatch.fnmatch(ename, name):
                return eid


class FindableMixin:
    # Note: you must define children() in the child class for this to work
    def find(self, name):
        eid = self._find(self.children(), name)
        if not eid:
            try:
                myname = self[PR_DISPLAY_NAME_W]
            except:
                myname = '(top)'
            raise Exception('no %r in %r' % (name, myname))
        return self.child(eid, name)

    def recursive_find(self, name):
        names = name.split('/')
        e = self
        for n in names:
            e = e.find(n)
        return e
        

class BaseProps:
    def __init__(self, pclass, propswanted, proplist):
        self.proporder = []
        self.propcache = {}
        self.pclass = pclass
        self.importprops(propswanted, proplist)

    def __getitem__(self, propid):
        if not propid in self.propcache:
            pidstr = mapitags.__dict__.get(propid)
            self.loadprops(pidstr or propid)
        return self.propcache[propid]

    def get(self, propid, default = None):
        try:
            return self.__getitem__(propid)
        except KeyError:
            return default

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

    def _addprop(self, k, kresult, v):
        if PROP_TYPE(kresult) == PT_ERROR:
            self.propcache[k] = None
        else:
            self.propcache[k] = v
        if not k in self.proporder:
            self.proporder.append(k)

    def importprops(self, propswanted, proplist):
        for k,(kresult,v) in zip(propswanted,proplist):
            self._addprop(k, kresult, v)



class Props(Mapi,BaseProps):
    def __init__(self, handle):
        Mapi.__init__(self, handle)
        BaseProps.__init__(self, self.__class__, [], [])
        self.propcache = {}

    def loadprops(self, *propids):
        ret, props = self.h.GetProps(propids)
        self.importprops(propids, props)

    def setprops(self, *props):
        # each prop is (pr_name, value)
        xprops = _lookup_custom_props_tuple(self.h, props)
        xprops = [(k,v) for k,v in xprops if v]
        #for k,v in xprops:
        #    print repr(((propnames.get(k), k), v))
        if xprops:
            self.h.SetProps(xprops)

    def save(self):
        self.h.SaveChanges(0)


class Message(Props):
    pass


class Table(Mapi):
    def __init__(self, pclass, ohandle, handle):
        Mapi.__init__(self, handle)
        self.ohandle = ohandle
        self.pclass = pclass
        
    def iter(self, *cols):
        self.h.SeekRow(mapi.BOOKMARK_BEGINNING, 0)
        if not cols:
            cols = self.h.QueryColumns(mapi.TBL_ALL_COLUMNS)
        xcols = list(_lookup_custom_props(self.ohandle, cols))
        self.h.SetColumns(xcols, 0)
        while 1:
            rows = self.h.QueryRows(1024, 0)
            for row in rows:
                yield BaseProps(self.pclass, cols, row)
            if not rows:
                break

    def __iter__(self):
        return self.iter()


class Container(Props,FindableMixin):
    def children(self):
        return Table(Container, self.h,
                     self.h.GetHierarchyTable(mapi.MAPI_UNICODE))

    def child(self, entryid, nicename):
        return Container(self._open(entryid, nicename))

    def subfolders(self):
        it = self.children().iter(PR_ENTRYID, PR_DISPLAY_NAME_W,
                                  PR_SUBFOLDERS)
        for eid,name,has_subfolders in it:
            yield eid,name,has_subfolders

    def messages(self):
        return Table(Message, self.h,
                     self.h.GetContentsTable(mapi.MAPI_UNICODE))

    def message(self, entryid, nicename):
        return Message(self._open(entryid, nicename))

    def newmessage(self):
        try:
            return Message(self.h.CreateMessage(None, 0))
        except Exception, e:
            raise OpenFailed("Can't create new message: %r" % e)


class Store(Props):
    def child(self, entryid, nicename):
        return Container(self._open(entryid, nicename))

    def root(self):
        return self.child(self[PR_IPM_SUBTREE_ENTRYID], 'root')

# Session
#    Stores
#       Root Container
#          Subfolder Containers
class Session(Mapi,FindableMixin):
    def __init__(self, hwnd = 0, profile = None, password = None):
        mapi.MAPIInitialize((mapi.MAPI_INIT_VERSION,0))
        flags = mapi.MAPI_EXTENDED
        if not profile:
            flags |= mapi.MAPI_USE_DEFAULT
        h = mapi.MAPILogonEx(hwnd, profile or '', password or '', flags)
        Mapi.__init__(self, h)
        # FIXME: avoid invalid memory access somewhere in win32com by
        # holding a reference to all the stores.  Don't know where that invalid
        # reference comes from, though...
        self.allstores = [self.store(row[PR_ENTRYID])
                          for row in self.stores().iter(PR_ENTRYID)]

    def stores(self):
        return Table(Store, self.h,
                     self.h.GetMsgStoresTable(0))

    def store(self, entryid):
        return Store(self.h.OpenMsgStore(0, entryid, None,
                        mapi.MDB_NO_DIALOG | mapi.MAPI_BEST_ACCESS))

    def children(self):
        return self.stores()

    def child(self, entryid, nicename):
        return self.store(entryid).root()

    def subfolders(self):
        for eid,name in self.stores().iter(PR_ENTRYID, PR_DISPLAY_NAME_W):
            yield eid,name,True
