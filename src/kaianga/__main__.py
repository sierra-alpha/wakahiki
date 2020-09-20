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
from threading import Event, Semaphore, Thread
import toml

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
    logformat = "[%(asctime)s] %(levelname)s:%(name)s:%(message)s"
    logging.basicConfig(level=getattr(logging, loglevel.upper()), stream=sys.stdout,
                        format=logformat, datefmt="%Y-%m-%d %H:%M:%S")


def expand_tilda(path, user):
    for x in path:
        if x.startswith(r"~/"):
            x.replace(r"~/", r"/home/{}/".format(user), 1)
    return path


i_o_sem = Semaphore()
task_change = Event()


def run_command(prompt, cmd):
    # add inputs
    shell_setting = prompt
    _logger.debug("running %s with prompt %s", cmd, shell_setting)
    if prompt:
        # Get prompt lock
        i_o_sem.acquire()
        output = subprocess.run(cmd, errors=True)
        i_o_sem.release()
        stderr = output.stderr
    else:
        stdout, stderr = subprocess.check_ouptut(cmd)

    if stderr:
        _logger.warning("error code {}". format(stderr))

        i_o_sem.acquire()
        print("{}".format(stderr))
        carry_on = input("There has been an error in {!r},"
                         " press q to quit or any key other"
                         " key to continue".format(cmd))

        if carry_on.lower == q:
            raise KeyboardInterrupt
        i_o_sem.release()

    elif not prompt:
        i_o_sem.acquire()
        print("{}".format(stdout))
        i_o_sem.release()


def process_command(task_name, task, running, executed, user):
    running.append(task_name)
    _logger.debug("Processing group {}".format(task_name))
    for x in task["scripts"]:
        run_command(
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

    while task_groups:
        tasks_started = False
        _logger.debug("to do tasks: {}".format(
            [x[0]for x in task_groups]))
        _logger.debug("running tasks: {}".format(running_tasks))
        _logger.debug("executed tasks: {}" .format(executed_groups))

        for task in task_groups:

            # If we're a pull repo task set up our pull script
            # if it hasn't been setup yet
            if ("script" not in task[1]
                  and "pull-repos" in task[0].split(".")[0]):
                task[1]["scripts"] = [ dict( script=(
                    ["git", "clone",
                     task[1][task[0].split(".")[1]]["url"],
                     str( Path(
                         task[1][task[0].split(".")[1]]["local"]
                     ).expanduser().absolute()
                     )]))]

            task_pre_reqs = task[1]["pre-reqs"]
            if set(task_pre_reqs).issubset(executed_groups):

                os.chdir(str(conf_file.parent))
                Thread(target=process_command, args=(
                    *task, running_tasks, executed_groups, user)).start()
                process_command
                task_groups.remove(task)
                tasks_started = True

        if not tasks_started:
            task_change.clear()
            # Wait for prompt lock here too
            _logger.info("waiting on pre-reqs to finish")
            _logger.debug("running tasks: {}".format(running_tasks))
            task_change.wait()


    _logger.info("script ends here")


if __name__ == "__main__":
    app()
