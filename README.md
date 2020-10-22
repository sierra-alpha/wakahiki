# Wakahiki

## Description

Wakahiki means [crane in Moari](https://maoridictionary.co.nz/search?idiom=&phrase=&proverb=&loan=&histLoanWords=&keywords=Wakahiki) 
and this wakahiki lifts up all your scripts specified in a 
config file, (examples to come but for now check out 
kaianga.conf in my kaianga repo) and executes them based on 
the priority order specified in the config file, it allows 
for sub tasks to be grouped together to execute inline if 
need be. It will also pick up and run multiple scripts in 
parrallel where possible.

## Installation

`pip install wakahiki`

Only tested in linux (debian) probably only relevant there two,
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
