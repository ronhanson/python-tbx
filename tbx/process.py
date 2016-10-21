#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: ai ts=4 sts=4 et sw=4 nu
"""
(c) 2013 - Ronan Delacroix
Process Utils
:author: Ronan Delacroix
"""

import os
import sys
import subprocess
import signal
import uuid as UUID
from datetime import datetime
import time
import tempfile
import threading
import re
import shutil
import atexit

import logging
from . import text as text_utils


def restart_program():
    """
    Restarts the current program.
    Note: this function does not return. Any cleanup action (like
    saving data) must be done before calling this function.
    """
    logging.debug("Restarting program...")
    python = sys.executable
    os.execl(python, python, * sys.argv)


def synchronized(lock):
    """
    Synchronization decorator; provide thread-safe locking on a function
    http://code.activestate.com/recipes/465057/
    """
    def wrap(f):
        def synchronize(*args, **kw):
            lock.acquire()
            try:
                return f(*args, **kw)
            finally:
                lock.release()
        return synchronize
    return wrap


def call_repeatedly(func, interval, *args, **kwargs):
    """
    Call a function at interval
    Returns both the thread object and the loop stopper Event.
    """
    main_thead = threading.current_thread()
    stopped = threading.Event()

    def loop():
        while not stopped.wait(interval) and main_thead.is_alive():  # the first call is in `interval` secs
            func(*args, **kwargs)

        return

    timer_thread = threading.Thread(target=loop, daemon=True)
    timer_thread.start()

    atexit.register(stopped.set)

    return timer_thread, stopped.set


def synchronized_limit(lock):
    """
    Synchronization decorator; provide thread-safe locking on a function
    http://code.activestate.com/recipes/465057/
    """
    def wrap(f):
        def synchronize(*args, **kw):
            if lock[1] < 10:
                lock[1] += 1
                lock[0].acquire()
                try:
                    return f(*args, **kw)
                finally:
                    lock[1] -= 1
                    lock[0].release()
            else:
                raise Exception('Too busy')
        return synchronize
    return wrap


def execute(command, return_output=True, log_file=None, log_settings=None, error_logfile=None, timeout=None, line_function=None, poll_timing = 0.01, logger=None, working_folder=None, env=None):
    """
        Execute a program and logs standard output into a file.

        :param return_output:      returns the STDOUT value if True or returns the return code
        :param logfile:            path where log file should be written ( displayed on STDOUT if not set)
        :param error_logfile:      path where error log file should be written ( displayed on STDERR if not set)
        :param timeout:            if set, it will kill the subprocess created when "timeout" seconds is reached. It will then raise an Exception.
        :param line_function:      set it to a "function pointer" for the function to be called each time a new line is written (line passed as a parameter).
        :param poll_timing:        wait time between timeout checks and std output check.

        :returns:   Standard output of the command or if return_output=False, it will give the "return code" of the command
    """

    tmp_log = False
    if log_settings:
        log_folder = log_settings.get('LOG_FOLDER')
    else:
        tmp_log = True
        log_folder = tempfile.mkdtemp()

    if not log_file:
        log_file = os.path.join(log_folder, "commands", "execute-command-logfile-%s.log" % UUID.uuid4())
        try:
            if not os.path.isdir(os.path.join(log_folder, "commands")):
                os.makedirs(os.path.join(log_folder, "commands"))
        except:
            pass
    if not logger:
        logger = logging.getLogger('command_execute')

    logfile_writer = open(log_file, 'a')
    header = "%s - Executing command (timeout=%s) :\n\t%s\n\n\n" % (datetime.now().isoformat(), timeout, command)
    logfile_writer.write(header)
    logfile_writer.flush()

    logfile_reader = open(log_file, 'rb')
    logfile_reader.seek(0, os.SEEK_END)
    logfile_start_position = logfile_reader.tell()

    if error_logfile:
        err_logfile_writer = open(error_logfile, 'a')
    else:
        err_logfile_writer = logfile_writer

    start = datetime.now()
    timeout_string = ""
    if timeout:
        timeout_string = "(timeout=%s)" % timeout
    logger.info(u"Executing command %s :\n\t\t%s" % (timeout_string, command) )

    # We use "exec <command>" as Popen launches a shell, that runs the command.
    # It will transform the child process "sh" into the "command exectable" because of the "exec".
    # Said more accuratly, it won't fork to create launch the command in a sub sub process.
    # Therefore, when you kill the child process, you kill the "command" process and not the unecessary "sh" parent process.
    if sys.platform != 'win32':
        command = u"exec %s" % text_utils.uni(command)
    process = subprocess.Popen(command, stdout=logfile_writer, stderr=err_logfile_writer, bufsize=1, shell=True, cwd=working_folder, env=env)

    while process.poll() == None:
        # In order to avoid unecessary cpu usage, we wait for "poll_timing" seconds ( default: 0.1 sec )
        time.sleep(poll_timing)

        # Timeout check
        if timeout != None:
            now = datetime.now()
            if (now - start).seconds> timeout:
                #process.terminate() ??
                os.kill(process.pid, signal.SIGKILL)
                os.waitpid(-1, os.WNOHANG)
                raise Exception("Command execution timed out (took more than %s seconds...)" % timeout)

        # Line function call:
        #   => if line_function is defined, we call it on each new line of the file.
        if line_function:
            o = text_utils.uni(logfile_reader.readline()).rstrip()
            while o != '':
                line_function(o)
                o = text_utils.uni(logfile_reader.readline()).rstrip()

    if not return_output:
        # Return result code and ensure we have waited for the end of sub process
        return process.wait()

    logfile_reader.seek(logfile_start_position, os.SEEK_SET) #back to the beginning of the file

    res = text_utils.uni(logfile_reader.read())

    try:
        logfile_reader.close()
        logfile_writer.close()
        err_logfile_writer.close()

        if tmp_log:
            shutil.rmtree(log_folder, ignore_errors=True)
    except:
        logger.exception("Error while cleaning after tbx.execute() call.")

    return res


def daemonize(umask=0, work_dir="/", max_fd=1024, redirect="/dev/null"):
    """
    When this function is called, the process is daemonized (by forking + killing its parent).
    It becomes a background task.
    It is useful to release the console.
    """
    if not redirect:
        redirect = "/dev/null"

    if hasattr(os, "devnull"):
        redirect = os.devnull

    try:
        pid = os.fork()
    except OSError as e:
        raise Exception("%s [%d]" % (e.strerror, e.errno))

    # first child
    if pid == 0:
        os.setsid()

        try:
            # Fork a second child.
            pid = os.fork()
        except OSError as e:
            raise Exception("%s [%d]" % (e.strerror, e.errno))

        # The second child.
        if pid == 0:
            os.chdir(work_dir)
            os.umask(umask)
        else:
            # exit first child
            os._exit(0)
    else:
        # Exit parent
        os._exit(0)

    #killing inherited file descriptors
    import resource
    maxfd = resource.getrlimit(resource.RLIMIT_NOFILE)[1]
    if maxfd == resource.RLIM_INFINITY:
        maxfd = max_fd

    # close all file descriptors.
    for fd in range(0, maxfd):
        try:
            os.close(fd)
        except OSError:
            # ignored
            pass

    os.open(redirect, os.O_RDWR) # standard input

    # Duplicate standard
    os.dup2(0, 1)			# standard output (1)
    os.dup2(0, 2)			# standard error (2)

    return os.getpid()


def is_running(process):
    s = subprocess.Popen(["ps", "axw"], stdout=subprocess.PIPE)
    for x in s.stdout:
        if re.search(process, x):
            return True
    return False


if __name__ == "__main__":
    import log
    log.configure_logging('process_test')

    COMMAND = """ifconfig {}""".format("-a -v")

    def show_address(line):
        if "inet " in line:
            addr = line.strip().split(' ')[1]
            print("### ADDRESS FOUND : {} ###".format(addr))

    result = execute(COMMAND, line_function=show_address)
    #print(result)
