# -*- coding: utf-8 -*-

"""The runner

Start a worker or a broker as a daemon.

Must be updated to work with multiple workers.

What do we need :

* the user ou userid
* the log file
* the error output
* the standard output
* the pid file
* the working directory

Based on the runner of python-daemon :

* Copyright © 2009–2010 Ben Finney <ben+python@benfinney.id.au>
* Copyright © 2007–2008 Robert Niederreiter, Jens Klein
* Copyright © 2003 Clark Evans
* Copyright © 2002 Noah Spurrier
* Copyright © 2001 Jürgen Hermann

"""

__license__ = """
    This file is part of RasPy.

    RasPy is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    RasPy is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with RasPy. If not, see <http://www.gnu.org/licenses/>.
"""
__copyright__ = "Copyright © 2013-2014 Sébastien GALLET aka bibi21000"
__author__ = 'Sébastien GALLET aka bibi21000'
__email__ = 'bibi21000@gmail.com'


import sys
import os
import os.path
import signal
import errno
import time
from daemon import pidlockfile
from daemon import DaemonContext
import pwd
import socket
from ConfigParser import SafeConfigParser

class RunnerError(Exception):
    """ Abstract base class for errors. """

class RunnerInvalidActionError(ValueError, RunnerError):
    """ Raised when specified action is invalid. """

class RunnerStartFailureError(RuntimeError, RunnerError):
    """ Raised when failure starting. """

class RunnerStopFailureError(RuntimeError, RunnerError):
    """ Raised when failure stopping. """

class Runner(object):
    """ Controller for a callable running in a separate background process.

        The first command-line argument is the action to take:

        * 'start': Become a daemon and call `app.run()`.
        * 'stop': Exit the daemon process specified in the PID file.
        * 'restart': Stop, then start.
        * 'status': Show the status of the process.

        """

    start_message = "started with pid %(pid)d"
    status_message_running = "process is running"
    status_message_not_running = "process is not running"

    def __init__(self, hostname=None, service="myrunnerinstance", \
            user=None, log_dir="/var/log", conf_dir="/etc", run_dir="/var/run", \
            context=None, endpoint_autoconf=None):
        """ Set up the parameters of a new runner.

            The `app` argument must have the following attributes:

            * `stdin_path`, `stdout_path`, `stderr_path`: Filesystem
              paths to open and replace the existing `sys.stdin`,
              `sys.stdout`, `sys.stderr`.

            * `pidfile_path`: Absolute filesystem path to a file that
              will be used as the PID file for the daemon. If
              ``None``, no PID file will be used.

            * `pidfile_timeout`: Used as the default acquisition
              timeout value supplied to the runner's PID lock file.

        """
        self.options = {}
        self.options_candidates = ['hostname', 'log_dir', 'run_dir', 'url_autoconf', 'user']
        self.options['hostname'] = socket.gethostname() if hostname == None else hostname
        self.options['service'] = service
        self.options['user'] = user
        self.options['log_dir'] = log_dir
        self.options['run_dir'] = run_dir
        self.options['conf_dir'] = conf_dir
        self.options['url_autoconf'] = url_autoconf
        self.options['context'] = context
        self.options['conffile_path'] = os.path.join(self.options['conf_dir'], self.options['service'] + ".ini")
        if os.path.isfile(self.options['conffile_path']):
            parser = SafeConfigParser()
            parser.read(self.options['conffile_path'])
            for candidate in self.options_candidates:
                if parser.has_option('Service', candidate):
                    self.options[candidate] = parser.get('Service', candidate)
        self.pidfile_timeout = 6.0
        self.stdout_path = os.path.join(self.options['log_dir'], self.options['service'] + "_out.log")
        self.stderr_path = os.path.join(self.options['log_dir'], self.options['service'] + "_err.log")
        self.pidfile_path = os.path.join(self.options['run_dir'], self.options['service'] + ".pid")
        if self.options['user'] and self.options['user'] != "":
            self.userid = pwd.getpwnam(self.options['user']).pw_uid
            if self.userid != os.getuid():
                #print self.userid
                os.setuid(self.userid)
        self.parse_args()
        self.pidfile = None
        if self.options['pidfile_path'] and self.options['pidfile_path'] != "":
            self.pidfile = make_pidlockfile(
                self.options['pidfile_path'], self.pidfile_timeout)
        if self.pidfile.is_locked() and not is_pidfile_stale(self.pidfile) \
          and self.action == 'start':
            print "Process already running. Exiting."
            sys.exit(1)
        if (not self.pidfile.is_locked() or is_pidfile_stale(self.pidfile)) \
          and (self.action == 'stop' or self.action == 'kill' or \
                self.action == 'restart'):
            print "Process not running. Exiting."
            sys.exit(1)

    def app_run(self):
        """
        The running process of the application
        """
        raise RunnerInvalidActionError("Action: %(action)r is not implemented" % vars(self))

    def app_shutdown(self):
        """
        The shutdown process of the application
        """
        raise RunnerInvalidActionError("Action: %(action)r is not implemented" % vars(self))

    def app_reload(self):
        """
        The reload process of the application
        """
        raise RunnerInvalidActionError("Action: %(action)r is not implemented" % vars(self))

    def _usage_exit(self, argv):
        """ Emit a usage message, then exit.
        """
        progname = os.path.basename(argv[0])
        usage_exit_code = 2
        action_usage = "|".join(self.action_funcs.keys())
        message = "usage: %(progname)s %(action_usage)s" % vars()
        emit_message(message)
        sys.exit(usage_exit_code)

    def parse_args(self, argv=None):
        """ Parse command-line arguments.
        """
        if argv is None:
            argv = sys.argv
        min_args = 2
        if len(argv) < min_args:
            self._usage_exit(argv)
        self.action = argv[1]
        if self.action not in self.action_funcs:
            self._usage_exit(argv)

    def _start(self):
        """ Open the daemon context and run the application.
        """
        self.daemon_context = DaemonContext()
        self.daemon_context.pidfile = self.pidfile
        #self.daemon_context.stdin = open(stdin_path, 'r')
        self.daemon_context.stdout = open(self.stdout_path, 'w+')
        self.daemon_context.stderr = open(self.stderr_path, 'w+', buffering=0)
        if is_pidfile_stale(self.pidfile):
            self.pidfile.break_lock()
        try:
            self.daemon_context.open()
        except pidlockfile.AlreadyLocked:
            pidfile_path = self.pidfile.path
            raise RunnerStartFailureError(
                "PID file %(pidfile_path)r already locked" % vars())
        pid = os.getpid()
        message = self.start_message % vars()
        emit_message(message, self.daemon_context.stdout)
        signal.signal(signal.SIGTERM, self.sigterm_handler)
        signal.signal(signal.SIGHUP, self.sighup_handler)
        self.app_run()

    def sigterm_handler(self, signal, frame):
        """
        """
        print 'TERM signal received : %s' % (signal)
        self.app_shutdown()
        sys.exit(0)

    def sighup_handler(self, signal, frame):
        """
        """
        print 'HUP signal received : %s' % (signal)
        self.app_reload()
        sys.exit(0)

    def _front(self):
        """ Open the daemon context and run the application.
        """
        if is_pidfile_stale(self.pidfile):
            self.pidfile.break_lock()
        pid = os.getpid()
        message = self.start_message % vars()
        emit_message(message, sys.stdout)
        signal.signal(signal.SIGINT, self.sigterm_handler)
        signal.signal(signal.SIGHUP, self.sighup_handler)
        self.app_run()

    def _terminate_daemon_process(self):
        """ Terminate the daemon process specified in the current PID file.
            """
        pid = self.pidfile.read_pid()
        try:
            os.kill(pid, signal.SIGTERM)
        except OSError, exc:
            raise RunnerStopFailureError(
                "Failed to terminate %(pid)d: %(exc)s" % vars())

    def _kill_daemon_process(self):
        """ Terminate the daemon process specified in the current PID file.
            """
        pid = self.pidfile.read_pid()
        try:
            os.kill(pid, signal.SIGKILL)
        except OSError, exc:
            raise RunnerStopFailureError(
                "Failed to kill %(pid)d: %(exc)s" % vars())

    def _stop(self):
        """ Exit the daemon process specified in the current PID file.
            """
        if not self.pidfile.is_locked():
            pidfile_path = self.pidfile.path
            raise RunnerStopFailureError(
                "PID file %(pidfile_path)r not locked" % vars())

        if is_pidfile_stale(self.pidfile):
            self.pidfile.break_lock()
        else:
            self._terminate_daemon_process()

    def _kill(self):
        """ Kill the daemon process specified in the current PID file.
            """
        if not self.pidfile.is_locked():
            pidfile_path = self.pidfile.path
            raise RunnerStopFailureError(
                "PID file %(pidfile_path)r not locked" % vars())

        if is_pidfile_stale(self.pidfile):
            self.pidfile.break_lock()
        else:
            self._kill_daemon_process()

    def _status(self):
        """ Show the status of the process.
            """
        if not self.pidfile.is_locked() or is_pidfile_stale(self.pidfile):
            emit_message(self.status_message_not_running)
        else:
            emit_message(self.status_message_running)

    def _restart(self):
        """ Stop, then start.
            """
        self._stop()
        time.sleep(self.pidfile_timeout)
        self._start()

    def _reload(self):
        """ reload application configuration.
            """
        self.app_reload()

    action_funcs = {
        'start': _start,
        'stop': _stop,
        'restart': _restart,
        'reload': _reload,
        'kill': _kill,
        'status': _status,
        'front': _front,
        }

    def _get_action_func(self):
        """ Return the function for the specified action.

            Raises ``RunnerInvalidActionError`` if the action is
            unknown.

            """
        try:
            func = self.action_funcs[self.action]
        except KeyError:
            raise RunnerInvalidActionError(
                "Unknown action: %(action)r" % vars(self))
        return func

    def do_action(self):
        """ Perform the requested action.
            """
        func = self._get_action_func()
        func(self)

def emit_message(message, stream=None):
    """ Emit a message to the specified stream (default `sys.stderr`). """
    if stream is None:
        stream = sys.stderr
    stream.write("%(message)s\n" % vars())
    stream.flush()

def make_pidlockfile(path, acquire_timeout):
    """ Make a PIDLockFile instance with the given filesystem path. """
    if not isinstance(path, basestring):
        error = ValueError("Not a filesystem path: %(path)r" % vars())
        raise error
    if not os.path.isabs(path):
        error = ValueError("Not an absolute path: %(path)r" % vars())
        raise error
    lockfile = pidlockfile.TimeoutPIDLockFile(path, acquire_timeout)
    return lockfile

def is_pidfile_stale(pidfile):
    """ Determine whether a PID file is stale.

        Return ``True`` (“stale”) if the contents of the PID file are
        valid but do not match the PID of a currently-running process;
        otherwise return ``False``.

        """
    result = False
    pidfile_pid = pidfile.read_pid()
    if pidfile_pid is not None:
        try:
            os.kill(pidfile_pid, signal.SIG_DFL)
        except OSError, exc:
            if exc.errno == errno.ESRCH:
                # The specified PID does not exist
                result = True
    return result
