import sys, os, errno


def unlink(filename):
    try:
        os.unlink(filename)
    except OSError, e:
        if e.errno != errno.ENOENT:  # if it doesn't exist, you're happy
            raise


def log(s):
    sys.stdout.flush()
    sys.stderr.write(s)
    sys.stderr.flush()

