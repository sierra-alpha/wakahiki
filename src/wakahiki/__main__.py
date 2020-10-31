# -*- coding: utf-8 -*-

#     wakahiki the crane that lifts and builds all your scripts
#     Copyright (C) 2020 Shaun Alexander

#     This program is free software: you can redistribute it and/or modify
#     it under the terms of the GNU General Public License as published by
#     the Free Software Foundation, either version 3 of the License, or
#     (at your option) any later version.

#     This program is distributed in the hope that it will be useful,
#     but WITHOUT ANY WARRANTY; without even the implied warranty of
#     MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#     GNU General Public License for more details.

#     You should have received a copy of the GNU General Public License
#     along with this program.  If not, see <https://www.gnu.org/licenses/>.

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

from wakahiki import __version__

__author__ = "Shaun Alexander"
__copyright__ = "Shaun Alexander"
__license__ = "gpl3"

_logger = logging.getLogger(__name__)


def setup_logging(loglevel, logfile):
    """Setup basic logging

    Args:
      loglevel (int): minimum loglevel for emitting messages
    """
    logformat = "[%(asctime)s] %(levelname)s:%(name)s:%(threadName)s:\n %(message)s"
    logging.basicConfig(
        filename=logfile, level=getattr(logging, loglevel.upper()),
        format=logformat, datefmt="%Y-%m-%d %H:%M:%S")
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(getattr(logging, loglevel.upper()))
    _logger.addHandler(handler)


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


def run_command(sudo, no_wait, prompt, cmd):
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
            stdout = (subprocess.check_output(
                cmd, text=True, stderr=subprocess.STDOUT)
                      if not no_wait else
                      subprocess.check_call(
                          cmd, text=True, stderr=subprocess.STDOUT)
            )
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
            x.get("no_wait", False),
            x.get("prompt", True),
            expand_tilda(x.get("script", ["echo", "'no script'"]), user)
        )
    running.remove(task_name)
    executed.append(task_name)
    task_change.set()


@click.command()
@click.option(
    "-c", "--conf-file", default="wakahiki.conf", show_default=True,
    help="The location of your config file"
)
@click.option(
    "-l", "--log-level", default="warning", show_default=True,
    help="The log levels to run at"
)
@click.option(
    "-o", "--output-file", default="wakahiki.log", show_default=True,
    help="The location of your config file"
)
@click.option(
    "-u", "--user", prompt="The user you want wakahiki to expand any ~ too",
    help="The user you want wakahiki to expand too (home)"
)
@click.option(
    "-v", "--verbose", is_flag=True, default=False,
    help="Set the output to verbose"
)
def app(conf_file, log_level, output_file, user, verbose):
    """Wakahiki app, Is the crane that picks up and builds all your scripts
    """

    if verbose and log_level.upper() != "DEBUG":
        log_level = "info"
    setup_logging(log_level, output_file)

    conf_file = Path(conf_file).expanduser().absolute()
    _logger.debug("reading config from {}, for user {}".format(
        conf_file, user))

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
           _logger.debug("executed tasks: {}" .format(
               executed_groups if len(executed_groups) == 1
               else [x for x in executed_groups if x])
           )
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

    _logger.info("Wakahiki completed successfully (doesn't mean all jobs were a success)")

if __name__ == "__main__":
    app()
