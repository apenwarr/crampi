default: all

all:
	@echo 'Try: make test'
	@echo ' or: make clean'
	
runtests:
	./wvtest.py t/tgitdb.py $(wildcard t/*.py)
	
test:
	./wvtestrun $(MAKE) runtests

clean:
	rm -f *.pyc *~ .*~ */*.pyc */*~ *.tmp *.sqlite3
