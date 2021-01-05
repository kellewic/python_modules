import fcntl, os.path, sys, tempfile

## Maintain a lock file to prevent scripts from running more than X times.
class lockfile(object):
    ENCODING = "utf-8"

    def __init__(self, path=None):
        if not path:
            path = "%s/%s.lock" % (tempfile.gettempdir().rstrip('/'), os.path.basename(sys.argv[0]).split('.')[0])

        self.path = path

    ## Check if lock file exists
    def exists(self):
        if os.path.isfile(self.path):
            return True
        return False

    ## Create lock file
    def create(self, max=1):
        fd = os.open(self.path, os.O_RDWR|os.O_CREAT)
        fcntl.flock(fd, fcntl.LOCK_EX)
        data = os.read(fd, 20)
        ret = True
        cur = 1

        if len(data) > 0:
            cur, max = str(data, self.ENCODING).strip().split(':')
            cur = int(cur)+1
            max = int(max)

            if cur > max: ret = False

        if ret is True:
            os.lseek(fd, 0, 0)
            os.write(fd, bytes("{}:{}".format(cur, max), self.ENCODING))

        fcntl.flock(fd, fcntl.LOCK_UN)
        os.close(fd)

        return ret

    ## Remove lock file
    def remove(self):
        try:
            fd = os.open(self.path, os.O_RDWR|os.O_CREAT)
            fcntl.flock(fd, fcntl.LOCK_EX)
            data = os.read(fd, 20)
            ret = True
            cur = 0
            max = 0

            if len(data) > 0:
                cur, max = data.split(':')
                cur = int(cur)-1
                max = int(max)

                if cur > 0: ret = False

            if ret is True:
                fcntl.flock(fd, fcntl.LOCK_UN)
                os.close(fd)
                os.unlink(self.path)

            else:
                os.lseek(fd, 0, 0)
                os.write(fd, bytes("{}:{}".format(cur, max), self.ENCODING))
                fcntl.flock(fd, fcntl.LOCK_UN)
                os.close(fd)

            return ret
        except:
            pass


def main(*args):
    ## Run 3 times in a row and last time it will error out
    lock_file = lockfile(path="/tmp/test_lockfile.lock")

    ## Allow 2 of this script to run
    if lock_file.create(max=2) is False:
        sys.stderr.write("WARN Script already running; shutting down\n")
        sys.exit()

    return 0


if __name__ == '__main__':
    sys.exit(main(*sys.argv))

