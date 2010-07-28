default: all

all: crampi
	@echo "Done."
	@echo
	@echo 'Now try: make test'
	@echo '     or: make clean'
	
crampi: crampi.py
	ln -sf crampi.py crampi
	
runtests:
	./wvtest.py t/tgitdb.py $(wildcard t/*.py)
	
test:
	./wvtestrun $(MAKE) runtests

clean:
	rm -f *.pyc *~ .*~ */*.pyc */*~ *.tmp crampi

distclean: clean
	rm -f *.sqlite3 *.db
