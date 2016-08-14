# -*- coding: utf-8 -*-
#!/usr/bin/python
import os
import codecs
import posixpath
import urllib.request
import cgi
import shutil
import mimetypes
import re
import platform
import collections
from collections import OrderedDict
import time
import nlp
import json

ostype = platform.system()

#coca 20000词频表路径和高阶词库路径
if ostype == "Windows":
	corpuspath = "coca-20000.txt"
	dictpath = "total.txt"
else:
	corpuspath = os.environ['OPENSHIFT_REPO_DIR'] + "coca-20000.txt"
	dictpath = os.environ['OPENSHIFT_REPO_DIR'] + "total.txt"

#读取词频表，注意要用list，保证次序（排名）
corpus_list = []
corpusfd = open(corpuspath, 'r', encoding='utf-8')
for corpusword in corpusfd.readlines():
	corpus_list.append(corpusword.strip('\n'))
print (len(corpus_list),"words have been read into memory.")
corpusfd.close()
#读取高阶词库，为了提高查找效率，这里使用dict_set，可以让效率提高7.7倍。
#也不要把这块代码放到analyzer函数里，那样耗费的时间会高出70多倍。
dictfd = open(dictpath, 'r', encoding='utf-8')#codecs.open(dictpath,"r","utf-8")
dict_list = []#词典单词列表
for dictword in dictfd.readlines():
	dict_list.append(dictword.strip('\n'))
dict_set = set(dict_list)
dictfd.close()
#
# IMPORTANT: Put any additional includes below this line.  If placed above this
# line, it's possible required libraries won't be in your searchable path
#

#这是提交页面
submitpage = '''<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta http-equiv="X-UA-Compatible" content="IE=edge,chrome=1">
  <title>Vocabulary Analyzer</title>
</head>
<body>
<h1 align="center">Vocabulary Analyzer V0.5</h1>
<p align="center"><B><font color="#0011ee">本工具由非营利英语学习论坛 EFL Club 出品，进入论坛请 <a href=\"http://forum.eflclub.me\" target=\"_blank\">点此链接</a></font></B></p>
<p>该在线工具可以对英文文本进行分析，提取出里面的高难度词汇。该工具是基于内置的词库来识别生词的,词库里面的单词是由专四、专八、托福、雅思、SAT、GRE的核心词汇表经过合并、排序、去重而来的，总计11567个单词，基本上全是比较难的词汇，但也不排除里面含有个别的四六级低阶词汇。</p>
<p>本工具同时内置了coca语料库中前20000个常用单词，会对提取出的单词按照常用程度排序。</p>
<p><i>2016-8-14日：重大升级，软件发生版本跳跃，版本号由 V0.3 跳跃到 V0.5，新增词形还原功能(lemmatization)，识别正确率提升 27.8%（处理速度略有降低，不过这么做很值得）</i></p>
<form method="post" action="" accept-charset="utf-8"> 
      <div style="text-align:center">
      <textarea name="inputtext" cols=130 rows=20 ></textarea>
      <p> 
         <input type="submit" value="请怒戳此按钮以便提交检测" style='font-size:29px' />
      </p>
      </div>
</form>
</body>
</html>'''
#这是结果页面
resultpage_part1 = '''<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta http-equiv="X-UA-Compatible" content="IE=edge,chrome=1">
  <title>Vocabulary Analyzer</title>
</head>
<body><div style="text-align:center">
<h1>以下单词被认为难度较大</h1>
<p>左侧为单词，右侧为频度排名，排名越小说明越常用，排名为0说明该单词不包括在20000词频表内。</p>
<hr>
'''
#中间拼接上结果，在拼接html结尾元素
resultpage_part2 = '''</div></body>
</html>'''

def application(environ, start_response):
	start_time = time.time()#计时起点
	###############
	print (environ['REQUEST_METHOD'],environ['PATH_INFO'])
	###############
	ctype = 'text/plain'
	if environ['PATH_INFO'] == '/health':
		response_body = "1"
	elif environ['PATH_INFO'] == '/env':
		response_body = ['%s: %s' % (key, value)
		                 for key, value in sorted(environ.items())]
		response_body = '\n'.join(response_body)
	############我的代码###########
	elif environ['REQUEST_METHOD'] == 'POST' :
		post_env = environ.copy()
		post_env['QUERY_STRING'] = ''
		post = cgi.FieldStorage(
		        fp=environ['wsgi.input'],
		        environ=post_env,
		        keep_blank_values=True
		)
		ctype = 'text/html'#这一行不加的话，浏览器直接显示出html源码，不渲染
		sourcestring = post['inputtext'].value
		#保留用户请求日志
		save_log(environ,sourcestring)
		#调用分析器
		result_dict = analyzer(sourcestring);
		#拼接html格式的结果
		resultcontent = ""
		for word,ranking in result_dict.items():
			resultcontent = resultcontent+word+"&nbsp"\
			        +str(ranking)+"<br>"

		tmplist = sourcestring.split(" ")
		total_number = len(tmplist)
		end_time = time.time()#计时终点
		response_body = resultpage_part1\
		        +u"<p>您的文本总共 "+str(total_number)\
		        +u" 个单词，分析用时 "+str(end_time-start_time)\
		        +" 秒，共匹配到 "+str(len(result_dict))+" 个生词</p>"\
		        + resultcontent\
		        +u"<hr><a href=\"/VocabularyAnalyzer\">Back</a>"\
		        +resultpage_part2
	elif environ['REQUEST_METHOD'] == 'GET' and environ['PATH_INFO'] == '/VocabularyAnalyzer':
		ctype = 'text/html'
		response_body = submitpage
	else:#GET /favicon.ico
		ctype = 'text/html'
		response_body = ""#这次的response_body没什么用
	response_body = response_body.encode('utf-8')	#Python3必加此行
	#########################################
	status = '200 OK'
	response_headers = [('Content-Type', ctype), ('Content-Length', str(len(response_body)))]
	#
	start_response(status, response_headers)
	return [response_body]

def analyzer(sourcestring):
	wordnet_tagged_dict = nlp.tokenizer(sourcestring)
	lemma_set = nlp.lemmatizer(wordnet_tagged_dict)
	#最终结果为有序字典result，便于后期对字典排序
	result_dict = collections.OrderedDict()
	for word in lemma_set:#对每一个待查词汇
		if word in dict_set:#如果它在高阶词典里
			try:
				ranking = corpus_list.index(word)#查找语料库排名
			except ValueError:#语料库不包含此单词
				ranking = -1
			result_dict[word] = ranking+1#下标加1为排名    
	#按照值排序
	result_dict = OrderedDict(sorted(result_dict.items(), key=lambda t: t[1]))
	return result_dict


#记录用户数据
def save_log(environ,sourcecontent):
	#http://stackoverflow.com/questions/7835030/，可以从HTTP_X_FORWARDED_FOR提取真实IP，但是不太好用。	#经过对Openshift日志文件app-root/logs/python.log的分析，发现除了HTTP_X_FORWARDED_FOR外，HTTP_X_REAL_IP也可以获得真实的IP地址，而且更简单。    
	try:
		user_ip = environ['HTTP_X_REAL_IP']
	except KeyError:
		user_ip = environ['REMOTE_ADDR']

	url = "http://freegeoip.net/json/%s" % user_ip
	u = urllib.request.urlopen(url)
	ip_info = u.read().decode('utf-8')
	u.close()
	json_extract = json.loads(ip_info)
	country = json_extract['country_name']
	region = json_extract['region_name']
	city = json_extract['city']
	#保存文件
	if ostype == "Windows":
		logpath = "log.txt"
	else:
		logpath = os.environ['OPENSHIFT_REPO_DIR'] + "log.txt"    
	logfd = open(logpath, "a", encoding='utf-8')
	logfd.write("User IP: "+user_ip+" "+country+","+region+","\
	            +city+"\nContent: "+sourcecontent+"\n\n")
	logfd.close()

#
# Below for testing only
#
if __name__ == '__main__':
	from wsgiref.simple_server import make_server
	#OpenShift已经自动配置好了端口转发，访问时不用加端口
	httpd = make_server('localhost', 8051, application)
	# Wait for a single request, serve it and quit.
	#httpd.handle_request()
	httpd.serve_forever()#这里改为永久运行
