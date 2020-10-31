# Wakahiki
[![Built with Spacemacs](https://cdn.rawgit.com/syl20bnr/spacemacs/442d025779da2f62fc86c2082703697714db6514/assets/spacemacs-badge.svg)](http://spacemacs.org)

<!-- markdown-toc start - Don't edit this section. Run M-x markdown-toc-refresh-toc -->
**Table of Contents**

- [Wakahiki](#wakahiki)
    - [Description](#description)
    - [Installation](#installation)
    - [Useage](#useage)
    - [Config](#config)
    - [Develop](#develop)

<!-- markdown-toc end -->


## Description

Wakahiki means [crane in Moari](https://maoridictionary.co.nz/search?idiom=&phrase=&proverb=&loan=&histLoanWords=&keywords=Wakahiki) 
and this wakahiki lifts up all your scripts specified in a 
config file, and executes them based on the priority order specified in the
config file, it allows for sub tasks to be grouped together to execute inline if 
need be. It will also pick up and run multiple scripts in parrallel where possible.

## Installation

`pip install wakahiki`

Only tested in linux (debian) probably only relevant there too,
potentially useful for other unix based OSes (MacOS etc)

Only tested in Python 3.7

## Useage

```shell
Usage: wakahiki [OPTIONS]

  Wakahiki app, Is the crane that picks up and builds all your scripts

Options:
  -c, --conf-file TEXT    The location of your config file  [default:
                          wakahiki.conf]

  -l, --log-level TEXT    The log levels to run at  [default: warning]
  -o, --output-file TEXT  The location of your config file  [default:
                          wakahiki.log]

  -u, --user TEXT         The user you want wakahiki to expand too (home)
  -v, --verbose           Set the output to verbose
  --help                  Show this message and exit.
```

## Config

wakahiki expects a config file populates with entries that look like the
following:

```toml
[command-group]
    pre-reqs = ["previous-command-group.scripts"]
    [[command-group.scripts]]
        no_wait = true
        prompt = true
        priority = 0
        root = true
        script = ["first", "group", "command"]
    [[command-group.scripts]]
        script = ["second", "group", "command"]
```

 - `[command-group]` (required) is the given name to the group of scripts to run, it is
   also used to to determine pre requisites, you can have multiple sections
   like this
 - `pre-reqs` (optional, default=None) the name of any script groups that should be run before this one,
   optional, if excluded will not depend on any other script groups before
   running but doesn't mean it will be first. At least one group must have no
   pre-req in order for the scripts to start.
 - `[[command-group.scripts]]` (required at least one) this is the sub group,
   allows you to specify order of script running for related subtasks, these are
   not run on multiple threads relative to other commands in the same subgroup
 - `no_wait` (optional, default=false) wakahiki will start the command in the
   background, usefull for launching daemon processes (will ignore this if set
   to run with prompt=true)
 - `prompt` (optional default=false) will run connected to the stdout/stderr and
   stdin so users can interact with the process as need be, processes that prompt
   users may cause the program to stop if this is not set to true.
 - `priority` (optional, default=0)will run the subgroups in this order,
   duplicate values are run in an undefined order amongst themselves but still
   in order relative to other values.
 - `root` (optional default=false) will run a sudo echo command before running
   the supplied command, the supplied commands still need to use sudo as
   required but this is to try and prompt once for many scripts that may require
   it.
 - `script` (required) the scripts you want to run in a format that a python
   `subprocess.run()` would expect to recieve, for example `["bash", "-c",
   "echo", "Hello World"]`

For a realworld example check out how it's used as part of the
[kainga](https://github.com/sierra-alpha/kainga) project, specifically the
kainga-conf
[here](https://github.com/sierra-alpha/kainga-conf/blob/master/kainga.conf) 

## Develop

If you wish to extend or improve wakahiki then the following will setup the
required dev environment and you can test changes whilst you develop 
by repeating the last command as needed after changing the source files. 

```bash
sudo apt-get update && sudo apt-get install -y python3 python3-pip git \
&& sudo pip3 install pipenv pyscaffold \
&& git clone https://github.com/sierra-alpha/kainga-conf.git \
&& mkdir wakahiki \
&& cd wakahiki \
&& virtualenv venv \
&& . venv/bin/activate \
&& git clone https://github.com/sierra-alpha/wakahiki.git \
&& cd wakahiki/ \
&& python setup.py develop \
&& python src/wakahiki -c ~/kainga-conf/kainga.conf -l debug -o ~/.wakahiki.log -u shaun
```
