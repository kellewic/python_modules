import logging, os.path, sys
from datetime import datetime
from multiprocessing import RLock

## Add these here so users don't have to import logging just to pass these
## values to the init method.
CRITICAL = logging.CRITICAL
ERROR = logging.ERROR
WARNING = logging.WARNING
INFO = logging.INFO
DEBUG = logging.DEBUG
NOTSET = logging.NOTSET

# next bit filched from Lib/logging/__init__.py who filched it from 1.5.2's inspect.py
def currentframe():
    """Return the frame object for the caller's stack frame."""
    try:
        raise Exception
    except:
        return sys.exc_info()[2].tb_frame.f_back

if hasattr(sys, '_getframe'): currentframe = lambda: sys._getframe(3)

_srcfile = os.path.normcase(currentframe.__code__.co_filename)
# done filching

## Wrapper around Python logging module to perform routine items like creating
## log directory, formatting, and file/console logging depending on value of 
## variable.
class Logger(logging.Logger):
    ## Recursive lock to allow multiple processes to share the logger
    rlock = RLock()

    ## Thin wrappers that use the rlock
    def log(self, lvl, msg, *args, **kwargs):
        if self.closed is False:
            self.rlock.acquire()
            super(Logger, self).log(lvl, msg, *args, **kwargs)
            self.rlock.release()

    def critical(self, msg, *args, **kwargs):
        self.log(CRITICAL, msg, *args, **kwargs)

    def error(self, msg, *args, **kwargs):
        self.log(ERROR, msg, *args, **kwargs)

    def warning(self, msg, *args, **kwargs):
        self.log(WARNING, msg, *args, **kwargs)

    def info(self, msg, *args, **kwargs):
        self.log(INFO, msg, *args, **kwargs)

    def debug(self, msg, *args, **kwargs):
        self.log(DEBUG, msg, *args, **kwargs)


    ## We need to override this or the filename equals logger.py since
    ## that is where the actual log() method is called. This is taken
    ## directly from Lib/logging/__init__.py
    def findCaller(self, stack_info=False):
        """
        Find the stack frame of the caller so that we can note the source
        file name, line number and function name.
        """
        f = currentframe()
        #On some versions of IronPython, currentframe() returns None if
        #IronPython isn't run with -X:Frames.
        if f is not None:
            f = f.f_back
        rv = "(unknown file)", 0, "(unknown function)", None
        while hasattr(f, "f_code"):
            co = f.f_code
            filename = os.path.normcase(co.co_filename)
            if filename == _srcfile:
                f = f.f_back
                continue
            sinfo = None
            if stack_info:
                sio = io.StringIO()
                sio.write('Stack (most recent call last):\n')
                traceback.print_stack(f, file=sio)
                sinfo = sio.getvalue()
                if sinfo[-1] == '\n':
                    sinfo = sinfo[:-1]
                sio.close()
            rv = (co.co_filename, f.f_lineno, co.co_name, sinfo)
            break
        return rv


    @classmethod
    def _get_name(cls, name):
        if name is None:
            ## Get the name of the script without the extension
            name = os.path.basename(sys.argv[0]).split('.')[0]

        return name


    def __init__(self, name=None, logdir=None, loglevel=logging.DEBUG, console=False, stderr=False, logThreads=0, logProcesses=0, logMultiprocessing=0):
        logging.Logger.__init__(self, Logger._get_name(name))
        self.closed = False

        ## Assume (and force) console output only
        if logdir is None:
            console = True
        else:
            ## Ensure our logging directory exists
            try:
                os.mkdir(logdir, 775)
            except OSError as e:
                if e.args[1] != 'File exists':
                    print("Cannot create {}: {}".format(logdir, e))
                    sys.exit(1)

            logdir = "{}/".format(logdir.rstrip('/'))
            # File to where we send this script's logs
            logging_output_file = "{}{}-{}.log".format(logdir, self.name, datetime.today().date())


        if console is True:
            if stderr is False:
                logging_output = sys.stdout
            else:
                logging_output = sys.stderr

            self.logfile = 'console'
        else:
            logging_output = open(logging_output_file, 'a')
            self.logfile = logging_output_file

        ## These enable/disable collecting of this log information
        logging.logThreads = logThreads
        logging.logProcesses = logProcesses
        logging.logMultiprocessing = logMultiprocessing

        self.setLevel(loglevel)

        logger_handler = logging.StreamHandler(logging_output)

        if logProcesses:
            logger_handler.setFormatter(logging.Formatter(
                "[%(asctime)s] %(name)s(%(process)d) %(levelname)s (%(filename)s "
                "=> %(lineno)s): %(message)s"
            ))
        else:
            logger_handler.setFormatter(logging.Formatter(
                "[%(asctime)s] %(name)s %(levelname)s (%(filename)s "
                "=> %(lineno)s): %(message)s"
            ))

        self.addHandler(logger_handler)

    ## Close underlying handlers if they support the close() method call
    def close(self):
        self.closed = True

        for handler in self.handlers:
            if hasattr(handler, "close"): 
                handler.close()


def main(*args):
    logger = Logger(logdir="/tmp", loglevel=DEBUG)
    logger.error("This is an error")
    return 0


if __name__ == '__main__':
    sys.exit(main(*sys.argv))

