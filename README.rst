=======
wakahiki
=======


Wakahiki means crane in Moari, and that's just what this package does,
it lifts up all your scritps and runs them in priority order on
multiple threads where possible.


Description
===========

Further documentation to follow, especially an example for the config
file required. You can group similar tasks that need to be in order
whilst having these tasks be part of a larger priority list that then
is used to determine the processing order. Scripts needing output and
user input need to be set to `prompt = true` in the config file as
this forces them to grab an IO lock to allow loical user interaction.
It uses the subprocess module to execute shell scripts or commands
entered into the config file.


Note
====

This project has been set up using PyScaffold 3.2.3. For details and usage
information on PyScaffold see https://pyscaffold.org/.
