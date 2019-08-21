python C:\Users\user\PycharmProjects\testFutu01\algoTrade.py SIMULATE 240262 HK.02822 2019-04-18 2019-04-18 200

pip list  #列出所有安装的库
pip list --outdated #列出所有过期的库
pip install --upgrade futu-api

import pip
from subprocess import call

for dist in pip.get_installed_distributions():
    call("pip install --upgrade " + dist.project_name, shell=True)