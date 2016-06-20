# -*- coding: utf-8 -*-
#装好gcc和gcc-c++，然后解压MBSP，进入目录后运行命令python setup.py，这样会自动编译完所有组件，注意不要加install参数，否则会将MBSP复制安装到site-packages目录。修改config.py文件将servers列表后两个元素删掉，这样就不用启用不必要的组件。另外autostart为True表示import MBSP时自动启动服务器，autostop为True表示Python退出时自动终止服务器，我们保持默认即可。注意将对于Openshift来说，Ports 15000 - 35530 are available for binding internal IP, but these ports are not externally addressable.[https://access.redhat.com/documentation/en-US/OpenShift_Online/2.0/html/User_Guide/sect-Binding_Applications_to_Ports.html]

#退到和MBSP同级目录（不然找不到MBSP模块），用Python命令行或者写个Python程序（例如这个程序），推送到Openshift就可以用了。
#本仓库中的MBSP目录是由MBSP.tar.gz解压而来，已经编译好，解压即用。
import os, sys;
import MBSP

#如果MBSP服务器没有启动则启动服务器，Python执行完毕后MBSP服务器不会关闭，这样以后就不用临时启动MBSP服务器了。
if not MBSP.config.autostart:
	MBSP.start()

def lemmatizer(sourcecontent):
	return MBSP.lemmatize(sourcecontent, tokenize=True)