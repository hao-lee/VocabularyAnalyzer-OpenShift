# -*- coding: utf-8 -*-
#装好gcc和gcc-c++，然后解压MBSP，进入目录后运行命令python setup.py，这样会自动编译完所有组件，注意不要加install参数，否则会将MBSP复制安装到site-packages目录。修改config.py文件将servers列表后两个元素删掉，这样就不用启用不必要的组件。另外autostart为True表示import MBSP时自动启动服务器，autostop为True表示Python退出时自动终止服务器，我们保持默认即可。注意将对于Openshift来说，Ports 15000 - 35530 are available for binding internal IP, but these ports are not externally addressable.[https://access.redhat.com/documentation/en-US/OpenShift_Online/2.0/html/User_Guide/sect-Binding_Applications_to_Ports.html]

#退到和MBSP同级目录（不然找不到MBSP模块），用Python命令行或者写个Python程序（例如这个程序），推送到Openshift就可以用了。
#本仓库中的MBSP目录是由MBSP.tar.gz解压而来，已经编译好，解压即用。
import os, sys;
import chardet
import MBSP
#如果MBSP服务器没有启动则启动服务器，Python执行完毕后MBSP服务器不会关闭，这样以后就不用临时启动MBSP服务器了。
#if not MBSP.config.autostart:
MBSP.start()

#输入处理前的单词列表，返回处理后的单词列表，如果需要处理的单词过多，MBSP会长时间无反应甚至直接崩溃，从而导致出现504超时错误，所以对于这种情况要分片处理。
def lemmatizer_main(sourcelist):
	list_length = len(sourcelist)
	#如果待处理单词少于500，直接处理，不分片；经测试，阀值为500时，处理用时似乎最少。
	if list_length <= 500:
		return lemmatizer_core(sourcelist)
	#分片
	result_list = []
	for i in range(0,list_length,500):
		sourcelist_slice = sourcelist[i:i+3]
		result_list += lemmatizer_core(sourcelist_slice)
	return result_list


#输入处理前的单词列表，返回处理后的单词列表
def lemmatizer_core(sourcelist_slice):
	#sourcecontent是列表，这里先转为字符串，以空格为分隔符
	input_str = ' '.join(sourcelist_slice)
	#如果向MBSP.lemmatize传递的字符串为空（当用户提交一句纯中文时），则MBSP会出现异常ValueError: list.index(x): x not in list。所以，此处检测一下，如果是空，那就随便赋值。
	if input_str == "":
		input_str = "abc"
	#MBSP.lemmatize返回值为MBSP.mbsp.TokenString类型，这是一种字符串的封装，所以在这里要转为普通字符串，不然analyzer函数里的lower函数不识别该类型。
	output_str = str(MBSP.lemmatize(input_str, tokenize=True))
	return output_str.split(' ')#切分成list返回