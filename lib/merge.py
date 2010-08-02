import time
from lib import entry


def run(g, el, branch, merged_refname, verbose,
        add_contact, update_contact, commit_contacts):
    a_id = g.commitid_lastmerge(refname=branch,
                                merged_refname=merged_refname)
    b_id = g.commitid_latest(merged_refname)
    print 'aid=%s bid=%s' % (a_id, b_id)
    a = entry.load_tree_from_commit(g, a_id)
    b = entry.load_tree_from_commit(g, b_id)
    nel = el.clone()
    for (lid,uuid,ed,ad,bd) in entry.merge(el, a, b):
        d = None
        e = None
        if not ed: # add
            mode = 'A'
            assert(bd)
            lid = add_contact(bd)
            e = entry.Entry(lid, uuid, bd)
            el.add(e)
        elif ad and not bd:  # del
            mode = 'D'
            e = el.uuids[uuid]
            # do nothing: deletes are too dangerous to merge
        elif ad != bd: # modify
            mode = 'M'
            e = el.uuids[uuid]
            changes = e.patch(ad, bd)
            if changes:
                update_contact(lid, e.d, changes)
        else:
            mode = ''
            e = el.uuids[uuid]
        if mode or verbose:
            print '%1s %s' % (mode, e)
    commit_contacts()
    el.save_commit(g, branch, merged_commit=b_id,
                   msg='merged from %s:%s..%s on %s'
                   % (merged_refname, a_id, b_id, time.asctime()))
