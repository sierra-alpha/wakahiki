This is the configuration file to bootstrap a system the way i like it.

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
