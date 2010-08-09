default: all

all: crampi
	
crampi: crampi.py
	ln -sf crampi.py crampi
	
runtests: all
	./wvtest.py t/tgitdb.py $(wildcard t/*.py)
	t/test.sh
	
test: all
	./wvtestrun $(MAKE) runtests

clean:
	rm -f *.pyc *~ .*~ */*.pyc */*~ *.tmp */*.tmp t/crampi.sqlite3 crampi

distclean: clean
	rm -f *.sqlite3 *.db
