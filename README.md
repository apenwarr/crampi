
Join the crampi mailing list:

 - Subscribe: send a message to crampi+subscribe@googlegroups.com
 - Post without subscribing: crampi@googlegroups.com
 - Read the archives: http://groups.google.com/group/crampi


CRAMPI: mixing up CRM and MAPI
==============================

Crampi is a tool for mixing up contacts (address book
entries) bidirectionally between two or more address books. 
Currently it supports these two address book storage
backends:

 - ffcrm: a driver for Fat Free CRM, an open source CRM
   (customer relationship management) tool written using
   Ruby on Rails
   
 - mapi: a driver for MAPI (Messaging API), Microsoft's
   standardized addressbook engine for Windows.  This has
   been tested with Exchange 2003, but probably works with
   other versions of Exchange, your personal Outlook
   contact list, and maybe even other MAPI-compliant
   servers like Lotus Notes.
   
It's relatively easy to add a new backend; look in
cmd/ffcrm.py or cmd/mapi.py for examples.


Quick start
-----------

WARNING!!  BACK UP YOUR DATABASES AND CONTACTS FOLDERS FIRST!!

On Linux with fat_free_crm installed:

	$ git clone git://github.com/apenwarr/crampi
	
	$ cd crampi
	
	$ make test
	   ... stop here if there are any errors! ...
	
	# import the initial fat_free_crm contact list
	$ ./crampi ffcrm -v -b fatfree ../fat_free_crm/db/development.sqlite3
	fe2e6f48-d67f-4d26-b691-d0dff72e9d81: John Doe
	fedcac68-fd57-484e-be5d-132be3aa1bba: Jimmy Jones
	   ... other entries ...
	1
	
	# incrementally import the contact list again
	$ ./crampi ffcrm -v -b fatfree ../fat_free_crm/db/development.sqlite3
	fe2e6f48-d67f-4d26-b691-d0dff72e9d81: John Doe
	fedcac68-fd57-484e-be5d-132be3aa1bba: Jimmy Jones
	   ... other entries ...
	2
	
	# show the list of existing branches (just one so far)
	$ ./crampi refs
	fatfree
	
	# show the history of the fatfree branch
	$ ./crampi log fatfree
	2 fatfree    exported from ffcrm '../fat_free_crm/db/development.sqlite3'
	1 fatfree    exported from ffcrm '../fat_free_crm/db/development.sqlite3'
	
	# count the entries in the fatfree branch
	$ ./crampi dump fatfree | grep ^email: | wc -l
	3607
	
	# import a different (empty) fat_free_crm database
	$ ./crampi ffcrm -v -b fatfree_empty \
		../fat_free_crm_empty/db/development.sqlite3
	3
	
	# count the entries in the fatfree_empty branch
	$ ./crampi dump fatfree_empty | wc -l
	0
	
	# merge the fatfree branch into fatfree_empty and
	# display the list of changes
	$ ./crampi ffcrm -v -b fatfree_empty \
		../fat_free_crm_empty/db/development.sqlite3 \
		-m fatfree
	4
	aid=None bid=2
	fe2e6f48-d67f-4d26-b691-d0dff72e9d81: John Doe
	fedcac68-fd57-484e-be5d-132be3aa1bba: Jimmy Jones
	   ... other entries ...
	5
	
	# show the updated history
	$ ./crampi log fatfree_empty
	5 fatfree_empty  merged from fatfree:None..2 on Mon Aug  9 19:15:36 2010
	4 fatfree_empty  exported from ffcrm '../fat_free_crm_empty/db/development.sqlite3'
	3 fatfree_empty  exported from ffcrm '../fat_free_crm_empty/db/development.sqlite3'
	
	# count the entries in the current fatfree_empty branch
	$ ./crampi dump fatfree_empty | grep ^email: | wc -l
	3607

On Windows with Outlook installed:

	> cd crampi
	
	# Get a list of available MAPI folders
	> c:\python26\python crampi mapi-ls
	Mailbox - Avery Pennarun
	Mailbox - Avery Pennarun/Contacts
	Mailbox - Avery Pennarun/Contacts/Junk
	   ... other entries ...
	Public Folders
	Public Folders/Favorites
	Public Folders/All Public Folders
	Public Folders/All Public Folders/Global Contacts
	   ... other entries ...
	
	# Import the global contacts folder with a bunch of items
	> c:\python26\python crampi mapi -v -b globalcontacts \
		"Public Folders/All Public Folders/Global Contacts"
	fe2e6f48-d67f-4d26-b691-d0dff72e9d81: John Doe
	fedcac68-fd57-484e-be5d-132be3aa1bba: Jimmy Jones
	   ... other entries ...
	1
	
	# Import an empty personal folder for testing
	> c:\python26\python crampi mapi -v -b junk \
		"Mailbox - Avery Pennarun/Contacts/Junk"
	2
	
	# Merge the global contacts into my personal test folder
	> c:\python26\python crampi mapi -v -b junk \   
		"Mailbox - Avery Pennarun/Contacts/Junk" \
		-m globalcontacts
	3
	aid=None bid=1
	fe2e6f48-d67f-4d26-b691-d0dff72e9d81: John Doe
	fedcac68-fd57-484e-be5d-132be3aa1bba: Jimmy Jones
	   ... other entries ...
	4
	
Feel free to play with variations of the above commands. 
It's safe to merge in both directions as many times as you
want.

But watch out!!  Be sure to make a backup of all your
databases / folders before you mess with them.  Crampi has
the potential to make a terrible mess if you use it wrong
or if it has bugs.  And this is an early version, so it
surely has bugs.

	
How it works
------------

Crampi's core data structure is a central sqlite3
"repository" called crampi.sqlite3.  This repository is
based roughly on the git (http://git-scm.com/) repository
structure, except less efficient and jammed into a sqlite3
database instead of directly onto the filesystem.  The main
reason for this is that crampi is intended to be able to
run on Windows as well as Unix, and git performs rather
badly on Windows, plus git is hard to install on Windows. 
Crampi has very few prerequisites so it's pretty easy to
get running on your Windows system.

Inside crampi.sqlite3, we store a the complete history
(including contents) of all the contact entries we've ever
imported from any of the address books being synced.  Once
upon a time, that would have been a horribly inefficient
thing to do; think of the many kilobytes of wasted space! 
But nowadays nobody cares, because you'd have to store an
awful lot of contact items to equal the size of a single
mpeg-encoded movie, and even a movie takes a tiny fraction
of your disk space.  On one corporate network I've seen, we
imported an Exchange Global Contacts folder with 3708
entries; it takes 4.7 megs, which is 0.0032% of my low-end
desktop PC's hard disk.  Big deal.

Anyway, inside the crampi repository is a set of
"branches." Each branch corresponds to the history of a
particular backend, such as a MAPI folder or an installed
copy of Fat Free CRM.  You can import into a branch as
often as you want, using the 'crampi ffcrm' or 'crampi mapi'
commands.

After importing all your branches, you can also merge the
changes from one branch to another.  Crampi uses the
repository to track which branches have been merged into
which other branches and what times, and it only merges the
particular attributes that of changesd in contacts that
have changed from one merge to the next.

For example, if you have a contact named Avery Pennarun,
and one person changes his email address using Fat Free
CRM, and another person changes his phone number in
Outlook, crampi will notice those two exact changes next
time you do a merge.  It'll then merge the two changes into
a single entry, and update both databases with the merged
data.  Neat, huh?

Let's not go into too much detail about the merge
algorithm, because it's complicated and confusing and not
that important to understand in detail right now.  But you
do have to remember one thing:

DON'T LOSE YOUR REPOSITORY DATABASE AFTER MERGING!

Crampi's repository is a little bit like git, but it's
very *unlike* git in one respect: not every backend it
talks to is a complete repository.  With git, if one guy
loses his repository, it's no big deal, because you can
just copy any other guy's repository and get the same
stuff.  With crampi, only the central repository has all
the history.  Other databases just track the latest version
of each contact, and they don't know anything about merges,
so if you lose your central crampi repository, future
merges will make a mess.  (Mostly they'll just cause
duplicate database entries.)

If you do lose the crampi repository, you're not totally
doomed; you'll probably just have to clean up some
duplicate items later.  You can use the 'crampi dedupe'
command to help with this.

Another thing you should know is that crampi can sync
between more than two repositories.  You can sync two
instances of Fat Free CRM (the contact information only,
not the notes and opportunities and so on).  Or you can
sync between two MAPI folders, like if you want to have a
personal contacts folder that's synced with the Global
Contacts folder (eg. if you're using a Blackberry and it
annoyingly refuses to sync your Global Contacts folder for
some reason).  Because of the way crampi works, you can add
synced folders at any time.


Installation Details - Windows
------------------------------

For the quickstart steps above to actually work on Windows,
you'll need to first install a copy of python, pywin32
(python and pywin32 are two different things), and crampi. 
The exact versions we used in testing are:

 - python-2.6.4.msi
 - pywin32-214.win32-py2.6.exe (pywin32-214.zip)
 - whatever version of crampi this README comes from
	
Make sure you've also installed Microsoft Outlook and
configured it with a default profile.  It's very important
that the default profile doesn't require you to enter a
password, because crampi won't pop up a password prompt!


Syncing between Unix and Windows
--------------------------------
	
It's possible to sync between Windows and Unix.  In fact,
that's most of the point!  If you have fat_free_crm, that's
probably running on Unix, and if you have MAPI
(Exchange/Outlook), that's probably running on Windows.  To
make it work, all you have to do is mount a shared folder
containing the crampi.sqlite3 file, then point crampi at it
using the --gitdb option.

If you don't look forward to setting up a Windows
workstation just to sync Exchange with your Unix system -
and who wants extra Windows systems?  Ew! - then you're in
luck.  Crossover Office 9.1.0 (http://www.codeweavers.com/)
works correctly with Microsoft Outlook 2003, Python 2.6,
pywin32, crampi, and Microsoft Exchange Server.  Earlier
versions of Crossover (I'm not sure exactly which ones)
have known crashiness issues when used with crampi, even
though they might work with Outlook by itself.  So make
sure you have at least 9.1.0.  You might also find that
other versions of Office work, but I haven't tested them,
so good luck.  You're better off to use exactly Outlook
2003.

It's also possible that the free versions of Wine (1.2.0 or
above) might work, assuming you can get Outlook 2003
installed and working.  I don't know; I've tried plain Wine
many times over the years and just got frustrated, and
Crossover relieved my frustration (mostly) for a lousy $40,
which was well worth it.  If you're not sure, you can
download their free demo and make sure it works for you
before forking over the cash.

After installing Outlook (and setting up a default Outlook
profile), python, and pywin32, you can then run crampi in
your Crossover Office session like this:

	$ cxoffice --bottle 'Microsoft Outlook 2003' --cx-app python \
		./crampi mapi-ls
		
Basically, wherever you might have typed

	> c:\python26\python crampi ...
	
at the DOS prompt, now you type

	$ cxoffice --bottle 'Microsoft Outlook 2003' --cx-app python \
		./crampi ...
		
at the Unix prompt, and it should work.

The really nice thing about running cxoffice under
Crossover is that you can now write a single
Unix shell script that syncs between fat_free_crm and MAPI. 
And you can set up that script to run from cron instead of
messing with the insane Windows Task Scheduler crap.

Just call the Unix version of crampi for fat_free_crm, and
the Windows version for MAPI.  They both write to the same
database, so refs/log/diff/dump/dedupe/etc all work with
either version.


Questions?  Comments?  Patches?
-------------------------------

This is an early release of crampi and surely has lots
of scary bugs.  Also, this documentation is probably
horribly incomplete.

Please send your questions/comments to the mailing list
shown at the top of this README.  (You don't have to be a
subscriber to send messages to the list.)

If you make patches to crampi for new features or bugfixes,
you can either mail them to the list with git
format-patch/send-email, or else fork the crampi project on
github.com and send a message to the list telling us what
you've added.

Enjoy!

Have fun,

Avery
