import fcntl, os.path, sys, tempfile

class lockfile(object):
    def __init__(self, path=None):
        if not path:
            path = "%s/%s.lock" % (tempfile.gettempdir().rstrip('/'), os.path.basename(sys.argv[0]).split('.')[0])

        self.path = path

    def exists(self):
        if os.path.isfile(self.path):
            return True
        return False

    def create(self, max=1):
        fd = os.open(self.path, os.O_RDWR|os.O_CREAT)
        fcntl.flock(fd, fcntl.LOCK_EX)
        data = os.read(fd, 20)
        ret = True
        cur = 1

        if len(data) > 0:
            cur, max = data.strip().split(':')
            cur = int(cur)+1
            max = int(max)

            if cur > max: ret = False

        if ret is True:
            os.lseek(fd, 0, 0)
            os.write(fd, "%s:%s" % (cur, max))

        fcntl.flock(fd, fcntl.LOCK_UN)
        os.close(fd)

        return ret


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
                os.write(fd, "%s:%s" % (cur, max))
                fcntl.flock(fd, fcntl.LOCK_UN)
                os.close(fd)

            return ret
        except:
            pass

