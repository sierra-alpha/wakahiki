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
import sys

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

@click.command()
@click.option(
    "-c", "--config", default="~/.config/kaianga/kaianga.conf", show_default=True,
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
def app(config, log_level, initial, user, verbose):
    """Kaianga app, bootstraps and refreshes home on demand
    """

    if verbose and log_level.upper() != "DEBUG":
        log_level = "info"
    setup_logging(log_level)

    if config.startswith(r"~/"):
        config = config.replace(r"~/", r"/home/{}/".format(user), 1)
    _logger.debug("reading config from %s for user %s %s mode:",
                  config, user, "in initial" if initial else "not in initial")

    _logger.info("script ends here")


if __name__ == "__main__":
    app()
