#!/usr/bin/env bash
. wvtest.sh
#set -e

TOP="$(pwd)"
cd t || exit 1

crampi()
{
    "$TOP/crampi" "$@"
}

WVSTART "init"
rm -f gitdb.sqlite3
cp sample/crm-demodata.db c1.tmp
cp sample/crm-demodata2.db c2.tmp
cp sample/crm-demodata3.db c3.tmp
cp sample/crm-empty.db ce.tmp

WVSTART "import"
WVPASS crampi ffcrm -b orig c1.tmp
WVPASS crampi ffcrm -b c1 c1.tmp
WVPASS crampi ffcrm -b c2 c1.tmp
WVPASS crampi ffcrm -b ce ce.tmp
WVPASSEQ "$(crampi dump ce)" ""
WVPASSNE "$(crampi dump c1)" ""
WVPASSNE "$(crampi dump c2)" ""

WVSTART "diff"
WVPASSEQ "$(crampi diff c1 c1)" ""
WVPASSEQ "$(crampi diff ce ce)" ""
WVPASSNE "$(crampi diff c1 ce)" ""
WVPASSNE "$(crampi diff ce c1)" ""

WVSTART "dedupe"
WVPASSEQ "$(crampi diff -s c1 c2 | wc -l)" "226"
WVPASS crampi dedupe c1 --using orig
WVPASS crampi dedupe c2 --using c1
WVPASSEQ "$(crampi diff c1 c2)" ""

WVSTART "log"
WVPASSEQ "$(crampi refs | wc -l)" "4"
WVPASSEQ "$(crampi log | wc -l)" "6"
WVPASSEQ "$(crampi log c2 | wc -l)" "2"

WVSTART "trivial merge"
WVPASS crampi ffcrm -b ce ce.tmp -m c1
WVPASSEQ "$(crampi diff c1 ce)" ""

WVSTART "harder merge"
WVPASSEQ "$(crampi diff c1 c2)" ""
WVPASS crampi ffcrm -b c2 c1.tmp -m c1
WVPASS crampi ffcrm -b c1 c1.tmp -m c2
WVPASSEQ "$(crampi diff c1 c2)" ""
# load the "updated" data (actually separate files, but crampi doesn't care)
WVPASS crampi ffcrm -b c2 c2.tmp
WVPASS crampi ffcrm -b c1 c3.tmp
WVPASSEQ "$(crampi diff -s c1 c2 | wc -l)" "1"
# merging c1 into c2 won't make it match; c2 still contains one change that
# doesn't match anybody else.
WVPASS crampi ffcrm -b c2 c2.tmp -m c1
WVPASSNE "$(crampi diff orig c2)" ""
WVPASSNE "$(crampi diff orig c1)" ""
WVPASSNE "$(crampi diff c1 c2)" ""
# but next we should merge the other way and it'll be fine
WVPASS crampi ffcrm -b c1 c1.tmp -m c2
WVPASSNE "$(crampi diff orig c2)" ""
WVPASSNE "$(crampi diff orig c1)" ""
WVPASSEQ "$(crampi diff c1 c2)" ""
# now make sure the merges actually updated the crm database files
WVPASS crampi ffcrm -b c1check c1.tmp
WVPASS crampi ffcrm -b c2check c2.tmp
WVPASS crampi dedupe c1check --using c1
WVPASS crampi dedupe c2check --using c1
WVPASSEQ "$(crampi diff c1 c1check)" ""
WVPASSEQ "$(crampi diff c2 c2check)" ""

WVSTART "validate"
WVPASS crampi validate
