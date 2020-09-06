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
import sys
import subprocess
import time
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

def run_command(root, prompt, cmd):
    command = "{}".format(cmd if not root
               else "echo 'entering root' "
               "&& su -c "
               "'{}' -m root".format(cmd))
    shell_setting = root or prompt
    import pdb; pdb.set_trace()
    subprocess.run(command, shell=shell_setting)

def process_command(task_name, task, running, executed_groups):
    # pre task work (is it a pull command?)
    try:
        for x in [v[0] for k,v in task.items() if k not in "priority pre-req".split()]:
            run_command(x["root"], True, x["script-path"])
    except:
        import pdb; pdb.set_trace()


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

    if conf_file.startswith(r"~/"):
        conf_file = conf_file.replace(r"~/", r"/home/{}/".format(user), 1)
    _logger.debug("reading config from %s for user %s %s mode:",
                  conf_file, user, "in initial" if initial else "not in initial")

    os.chdir("/{}".format("/".join(conf_file.split("/")[:-1])))
    _logger.debug("changed to directory %s", os.getcwd())
    user_config = toml.load(conf_file)

    # build default attributes

    # ordered_config = prioritise(user_config)
    # figure out order
    task_groups ={
        "{}.{}".format(x,z):{
            z:y[z],
            "priority": y.get("priority", float("inf")),
            "pre-req": y.get("pre-req", None),
        }
        for x,y in user_config.items()
        for z in y.keys()
        if z.lower() not in "priority pre-req".split()
    }

    sorted_tasks = sorted(list(task_groups.items()),
                          key=lambda x: x[1]["priority"]
    )
    executed_groups = [None]
    running_tasks = []

    while len(sorted_tasks) > 0:
        current_prioirity = sorted_tasks[0][1]["priority"]
        tasks_started = False
        for i in range(len(sorted_tasks)-1):
            task_priority = sorted_tasks[i][1]["priority"]
            task_pre_req = sorted_tasks[i][1]["pre-req"]
            if task_priority <= current_prioirity and task_pre_req in executed_groups:

                # Marks when done and blocks if need be
                process_command(*sorted_tasks.pop(0), running_tasks, executed_groups)
                tasks_started = True

        if not tasks_started:
            _logger.debug("waiting on tasks %s, completed %s",
                          ", ".join(running_tasks), ", ".join(executed_groups[1:])
                          if executed_groups > 1 else "None")
            sleep(2)


    # run process, if it's blocking then wait till end

    import pdb; pdb.set_trace()

    _logger.info("script ends here")


if __name__ == "__main__":
    app()
