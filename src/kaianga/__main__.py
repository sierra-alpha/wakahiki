# -*- coding: utf-8 -*-
"""
This is a skeleton file that can serve as a starting point for a Python
console script. To run this script uncomment the following lines in the
[options.entry_points] section in setup.cfg:

    console_scripts =
         fibonacci = kaianga.skeleton:run

Then run `python setup.py install` which will install the command `fibonacci`
inside your current environment.
Besides console scripts, the header (i.e. until _logger...) of this file can
also be used as template for Python modules.

Note: This skeleton file can be safely removed if not needed!
"""

import click
import logging
import numbers
import os
from pathlib import Path
import sys
import subprocess
import time
import _thread
import threading
import toml
import traceback

from kaianga import __version__

__author__ = "Shaun Alexander"
__copyright__ = "Shaun Alexander"
__license__ = "gpl3"

_logger = logging.getLogger(__name__)


def setup_logging(loglevel):
    """Setup basic logging

    Args:
      loglevel (int): minimum loglevel for emitting messages
    """
    logformat = "[%(asctime)s] %(levelname)s:%(name)s:%(threadName)s:\n %(message)s"
    logging.basicConfig(level=getattr(logging, loglevel.upper()), stream=sys.stdout,
                        format=logformat, datefmt="%Y-%m-%d %H:%M:%S")


def expand_tilda(path, user):
    return [x.replace(r"~/", r"/home/{}/".format(user), 1)
            if x.startswith(r"~/") or r" ~/" in x
            else x for x in path]


i_o_sem = threading.Semaphore()
task_change = threading.Event()
exit_call = threading.Event()


def check_exit_get_sem():
    i_o_sem.acquire()
    if exit_call.is_set():
        return
    else:
        _logger.debug("exit flag set, exiting thread")
        i_o_sem.release()
        sys.exit()


def carry_on_q(err, cmd):
    """Need to get IO sem before calling here"""

    _logger.warning("error code {}". format(err))
    carry_on = input(
        "There has been an error in {!r}, press q to quit or any other"
        " key to try and continue: ".format(cmd))

    if carry_on.lower() == "q":
        if threading.current_thread() != threading.main_thread():
            _logger.debug(
                "exiting thread - {!r}"
                .format(threading.current_thread()))
            _logger.info("exiting to __main__")
            _thread.interrupt_main()
            exit_call.clear()
            i_o_sem.release()
            sys.exit()
        else:
            exit_call.clear()
            i_o_sem.release()
            raise KeyboardInterrupt
    i_o_sem.release()


def go_sudo(cmd):
    print("Going sudo for {}".format(cmd))
    check_exit_get_sem()
    output = subprocess.run(["sudo", "echo", "'entered sudo succesfully'"], errors=True)
    stderr = output.stderr or output.returncode
    i_o_sem.release()
    return output, stderr


def run_command(sudo, prompt, cmd):
    # add inputs
    shell_setting = prompt
    stderr = None
    check_exit_get_sem()
    _logger.debug("running %s with prompt %s", cmd, shell_setting)
    i_o_sem.release()
    if prompt:
        # Get prompt lock
        check_exit_get_sem()
        try:
            output = subprocess.run(cmd, errors=True)
            stderr = output.stderr or output.returncode
            i_o_sem.release() if not stderr else None
        except (FileNotFoundError, subprocess.CalledProcessError):
            # get sem here to go through into carry on q below
            check_exit_get_sem()
            stderr = traceback.format_exc()

    else:
        try:
            if sudo:
                output, stderr = go_sudo(cmd)
            stdout = subprocess.check_output(
                cmd, text=True, stderr=subprocess.STDOUT)
        except (FileNotFoundError, subprocess.CalledProcessError):
            # get sem here to go through into carry on q below
            check_exit_get_sem()
            stderr = traceback.format_exc()

    if stderr:
        # Need to get the IO sem where the exception happens to stop
        # other output getting printed in between error and prompt
        carry_on_q(stderr, cmd)

    elif not prompt:
        check_exit_get_sem()
        print("call returned from: {}".format(cmd))
        print("{}".format(stdout if stdout else "success"))
        i_o_sem.release()


def process_command(task_name, task, running, executed, user):
    running.append(task_name)
    i_o_sem.acquire()
    _logger.debug("Processing group {}".format(task_name))
    i_o_sem.release()
    for x in task["scripts"]:
        run_command(
            x.get("root", False),
            x.get("prompt", True),
            expand_tilda(x.get("script", ["echo", "'no script'"]), user)
        )
    running.remove(task_name)
    executed.append(task_name)
    task_change.set()


@click.command()
@click.option(
    "-c", "--conf_file", default="~/.config/kaianga/kaianga.conf", show_default=True,
    help="The location of your config file"
)
@click.option(
    "-l", "--log_level", default="warning", show_default=True,
    help="The log levels to run at"
)
@click.option(
    "-i", "--initial", is_flag=True, default=False,
    help="The initial run will run the run_only_once part of the kaianga.conf"
)
@click.option(
    "-u", "--user", prompt="The user you want to set up as your kaianga",
    help="The user you want to set up as your kaianga (home)"
)
@click.option(
    "-v", "--verbose", is_flag=True, default=False,
    help="Set the output to verbose"
)
def app(conf_file, log_level, initial, user, verbose):
    """Kaianga app, bootstraps and refreshes home on demand
    """

    if verbose and log_level.upper() != "DEBUG":
        log_level = "info"
    setup_logging(log_level)

    conf_file = Path(conf_file).expanduser().absolute()
    _logger.debug("reading config from {}, for user {}, {} mode:".format(
        conf_file, user, "in initial" if initial else "not in initial"))

    os.chdir(str(conf_file.parent))
    _logger.debug("changed to directory %s", os.getcwd())
    user_config = toml.load(conf_file)

    # build default attributes

    # ordered_config = prioritise(user_config)
    # figure out order
    task_groups = list( {
        "{}.{}".format(x,z):{
            z:y[z],
            "pre-reqs": y.get("pre-reqs", [None]),
        }
        for x,y in user_config.items()
        for z in y.keys()
        if z.lower() not in ["pre-reqs"]
    }.items() )

    # sorted_tasks = sorted(list(task_groups.items()),
    #                       key=lambda x: x[1]["priority"]
    # )
    executed_groups = [None]
    running_tasks = []
    waits = 0
    exit_call.set()
    thread_collect = []

    try:
       while task_groups:
           tasks_started = False
           i_o_sem.acquire()
           _logger.debug("to do tasks: {}".format(
               [x[0]for x in task_groups]))
           _logger.debug("running tasks: {}".format(running_tasks))
           _logger.debug("executed tasks: {}" .format(executed_groups))
           i_o_sem.release()

           for task in task_groups:

               task_pre_reqs = task[1]["pre-reqs"]
               if set(task_pre_reqs).issubset(executed_groups):

                   os.chdir(str(conf_file.parent))
                   this_thread = threading.Thread(
                       target=process_command, name=task[0], args=(
                       *task, running_tasks, executed_groups, user))
                   thread_collect.append(this_thread)
                   this_thread.start()
                   task_groups.remove(task)
                   tasks_started = True

           if not tasks_started:
               task_change.clear()
               i_o_sem.acquire()
               _logger.info("waiting on pre-reqs to finish")
               _logger.debug("running tasks: {}".format(running_tasks))

               if waits == 3:
                   carry_on = input(
                       "It seems like pre-reqs have failed, do you want to quit?"
                       " q to quit, any other key to continue: ")
                   if carry_on.lower() == "q":
                       exit_call.clear()
                       i_o_sem.release()
                       raise KeyboardInterrupt
                   waits = 0
               i_o_sem.release()

               if not task_change.wait(timeout=10):
                   waits += 1

       i_o_sem.acquire()
       _logger.debug("Collecting any still running threads")
       _logger.debug("running tasks: {}".format(running_tasks))
       i_o_sem.release()

       for t in thread_collect:
           while t.is_alive():
               t.join(10)
               if t.is_alive():
                   i_o_sem.acquire()
                   _logger.debug("waiting on running tasks: {}".format(running_tasks))
                   i_o_sem.release()


    except KeyboardInterrupt:
       i_o_sem.acquire()
       _logger.debug("in __main__ cleaning up other threads")
       exit_call.clear()
       i_o_sem.release()
       raise KeyboardInterrupt

    _logger.info("Kaianga completed successfully (doesn't mean all jobs were a success)")

if __name__ == "__main__":
    app()
