import yaml, copy

class Entry:
    def __init__(self, lid, uuid, d):
        self.lid = lid
        self.uuid = uuid
        self.d = copy.deepcopy(d)

    def to_yaml(self):
        return yaml.safe_dump(self.d, default_flow_style=False)


class Entries:
    def __init__(self, entries):
        self.entries = list(entries)
        self.lids = self.uuids = None  # no indexes by default

    def clone(self):
        return Entries([Entry(e.lid,e.uuid,copy.deepcopy(e.d))
                        for e in self.entries])

    def reindex(self):
        self.lids = {}
        self.uuids = {}
        for e in self.entries:
            if e.uuid:
                assert(not e.uuid in self.uuids)
                self.uuids[e.uuid] = e
            if e.lid:
                assert(not e.lid in self.lids)
                self.lids[e.lid] = e

    def uuids_from_commit(self, gdb, refname):
        commitid = gdb.commitid_latest(refname)
        if commitid:
            (r, tree, localids, merged_commit) = gdb.commit(commitid)
            for e in self.entries:
                if not e.uuid:
                    e.uuid = localids.get(e.lid)

    def assign_missing_uuids(self, gdb):
        for e in self.entries:
            if not e.uuid:
                e.uuid = gdb.uuid_new()

    def save_tree(self, gdb):
        blobs = {}
        for e in self.entries:
            assert(e.uuid)
            assert(e.lid)
            blobs[e.uuid] = gdb.blob_set(e.to_yaml())
        return gdb.tree_set(blobs)

    def save_commit(self, gdb, refname, merged_commit = None):
        localids = []
        for e in self.entries:
            assert(e.lid)
            assert(e.uuid)
            localids.append((e.lid, e.uuid))
        return gdb.commit_set(refname, self.save_tree(gdb), localids,
                              merged_commit = merged_commit)


def _load_tree(gdb, treeid):
    for (uuid,blobid) in gdb.tree(treeid).iteritems():
        d = yaml.safe_load(gdb.blob(blobid))
        yield Entry(None,uuid,d)


def load_tree(gdb, treeid):
    return Entries(_load_tree(gdb, treeid))


def _compare(cur, a, b):
    curkeys = set(cur)
    akeys = set(a)
    bkeys = set(b)

    added = (bkeys - akeys) - curkeys
    deleted = (akeys - bkeys) & curkeys
    same = curkeys - added - deleted
    return (same, added, deleted)


def merge(cur, a, b):
    cur.reindex()
    a.reindex()
    b.reindex()
    (same, added, deleted) = _compare(cur.uuids.keys(),
                                      a.uuids.keys(),
                                      b.uuids.keys())

    r = Entries([])
    for e in cur.entries:
        if not e.uuid in deleted:
            ae = a.uuids.get(e.uuid)
            be = a.uuids.get(e.uuid)
            if be and (not ae or ae.d != be.d):
                d = b.uuids[e.uuid].d  # FIXME merge individual elements?
            else:
                d = e.d
            r.entries.append(Entry(e.lid, e.uuid, d))
    for uuid in added:
        be = b.uuids[uuid]
        r.entries.append(Entry(None, uuid, be.d))
    return r
