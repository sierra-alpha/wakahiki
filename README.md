This is the configuration file to bootstrap a system the way i like it.
Commands expect to be in a `bash` shell, default is `sh` enter bash then,
Copy and paste the following into a containers shell. the &&'s allow for commands requiring input.

```bash
sudo apt-get update && sudo apt-get install -y python3 python3-pip git \
&& sudo pip3 install pipenv pyscaffold \
&& git clone https://github.com/sierra-alpha/kaianga-conf.git \
&& mkdir kaianga \
&& cd kaianga \
&& virtualenv venv \
&& . venv/bin/activate \
&& git clone https://github.com/sierra-alpha/kaianga.git \
&& cd kaianga/ \
&& python setup.py develop \
&& python src/kaianga -c ~/kaianga-conf/kaianga.conf -i -l debug -u shaun
```

Or the following
```bash
sudo apt-get update && sudo apt-get install -y python3 python3-pip git \
&& git clone https://github.com/sierra-alpha/kaianga-conf.git \
&& export PATH="$(python3 -m site --user-base)/bin:$PATH" \
&& pip3 install -i https://test.pypi.org/simple/ kaianga \
&& kaianga -c ~/kaianga-conf/kaianga.conf -i -l debug -u shaun
```

or in an .xinitrc
```bash
xterm -e bash -c "sudo apt-get update \
&& sudo apt-get install -y python3 python3-pip git \
&& git clone https://github.com/sierra-alpha/kaianga-conf.git \
|| cd kaianga-conf && git pull \
&& export PATH=\"$(python3 -m site --user-base)/bin:$PATH\" \
&& pip3 install -U -i https://test.pypi.org/simple kaianga \
&& kaianga -c ~/kaianga-conf/kaianga.conf -i -l debug -u shaun \
&& emacsclient -c -a emacs \
|| echo Failure, enter to exit && read ; bash"
```
