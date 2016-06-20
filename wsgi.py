# -*- coding: utf-8 -*-
#!/usr/bin/python
import os
import codecs
import posixpath
import BaseHTTPServer
import urllib
import cgi
import shutil
import mimetypes
import re
import platform
import collections
from collections import OrderedDict
import urllib2
import time
import lemmatizer

#部署到OpenShift时需要下面else语句里面的这几行
ostype = platform.system()
if ostype == "Windows":
    pass
else:
    virtenv = os.environ['OPENSHIFT_PYTHON_DIR'] + '/virtenv/'
    virtualenv = os.path.join(virtenv, 'bin/activate_this.py')
    try:
	execfile(virtualenv, dict(__file__=virtualenv))
    except IOError:
	pass

#coca 20000词频表路径和高阶词库路径
if ostype == "Windows":
    corpuspath = "coca-20000.txt"
    dictpath = "total.txt"
else:
    corpuspath = "/var/lib/openshift/5749a7f30c1e66521c000168/app-root/runtime/repo/coca-20000.txt"
    dictpath = "/var/lib/openshift/5749a7f30c1e66521c000168/app-root/runtime/repo/total.txt"

#读取词频表，注意要用list，保证次序（排名）
corpuslist = []
corpusfd = open(corpuspath, 'r')
for corpusword in corpusfd.readlines():
    corpuslist.append(corpusword.strip('\n'))
print len(corpuslist),"words have been read into memory."
corpusfd.close()
#读取高阶词库，为了提高查找效率，这里使用dict_set，可以让效率提高7.7倍。
#也不要把这块代码放到analyzer函数里，那样耗费的时间会高出70多倍。
dictfd = open(dictpath, 'r')#codecs.open(dictpath,"r","utf-8")
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
<h1 align="center">Vocabulary Analyzer V0.3</h1>
<p align="center"><B><font color="#0011ee">本工具由非营利英语学习论坛 EFL Club 出品，进入论坛请 <a href=\"http://forum.eflclub.me\" target=\"_blank\">点此链接</a></font></B></p>
<p>该在线工具可以对英文文本进行分析，提取出里面的高难度词汇。该工具是基于内置的词库来识别生词的,词库里面的单词是由专四、专八、托福、雅思、SAT、GRE的核心词汇表经过合并、排序、去重而来的，总计11567个单词，基本上全是比较难的词汇，但也不排除里面含有个别的四六级低阶词汇。</p>
<p>Tips:因为英语文本中的单词有很多都不是原形形态，而词库中都是原形，所以会有一些单词匹配不上，为了达到更好的识别效果需要将文本进行lemmatize（词形还原）。
请打开<a href=\"http://textanalysisonline.com/mbsp-word-lemmatize\" 
target=\"_blank\">词形还原工具</a>，将文本复制进去并点击\"MBSP Word 
Lemmatize\"，结果中右侧的文本就是还原后的。对还原后的文本使用本站工具进行检测会极大的提高识别率！</p>
<p>本工具同时内置了coca语料库中前20000个常用单词，会对提取出的单词按照常用程度排序。</p>
<form method="post" action=""> 
      <div style="text-align:center">
      <textarea name="inputtext" cols=130 rows=20 >粘贴文本</textarea>
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
    start_time = time.clock()#计时起点
    ###############
    print environ['REQUEST_METHOD'],environ['PATH_INFO']
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
	result = analyzer(sourcestring);
	resultcontent = ""
	for word,ranking in result.iteritems():
	    resultcontent = resultcontent+word+"&nbsp"\
	        +str(ranking)+"<br>"
	
	tmplist = sourcestring.split(" ")
	total_number = len(tmplist)
	end_time = time.clock()#计时终点
	response_body = resultpage_part1\
	    +"<p>您的文本总共 "+str(total_number)\
	    +" 个单词，分析用时 "+str(end_time-start_time)+" 秒</p>"\
	    + resultcontent\
	    +"<hr><a href=\"/VocabularyAnalyzer\">Back</a>"\
	    +resultpage_part2
    elif environ['REQUEST_METHOD'] == 'GET' and environ['PATH_INFO'] == '/VocabularyAnalyzer':
        ctype = 'text/html'
        response_body = submitpage
    else:#GET /favicon.ico
	ctype = 'text/html'
	response_body = ""#这次的response_body没什么用
    #########################################
    status = '200 OK'
    response_headers = [('Content-Type', ctype), ('Content-Length', str(len(response_body)))]
    #
    start_response(status, response_headers)
    return [response_body]

def analyzer(sourcestring):
    #使用正则表达式，把单词提出出来，并都修改为小写格式，返回列表类型
    sourcelist = re.findall("\w+",str.lower(sourcestring))
    #去除列表中的重复项，《双城记》经过去重后单词数目由139461变为9951
    sourcelist = set(sourcelist)
    #去除含有的数字和符号
    sourcelist_tmp = []
    for sourceword in sourcelist:
	m = re.search("\d+",sourceword)
	n = re.search("\W+",sourceword)
	#if not m and  not n and len(i)>4:
	if not m and  not n:
	    sourcelist_tmp.append(sourceword)
    sourcelist = sourcelist_tmp
    #词形还原
    if ostype == "Windows":
	#Windows上MBSP没法用，所以本地测试时不进行lemmatize
	pass
    else:
	#lemmatization，传入list，返回值也是list，只不过词形被还原了
	sourcelist = lemmatizer.lemmatizer(sourcelist)    
    #最终结果为有序字典result，便于后期对字典排序
    result = collections.OrderedDict()
    print(type(sourcelist))
    for word in sourcelist:#对每一个待查词汇
	if word in dict_set:#如果它在高阶词典里
	    try:
		ranking = corpuslist.index(word)#查找语料库排名
	    except ValueError:#语料库不包含此单词
		ranking = -1
	    result[word] = ranking+1#下标加1为排名    
    #按照值排序
    result = OrderedDict(sorted(result.items(), key=lambda t: t[1]))
    return result


#记录用户数据
def save_log(environ,sourcecontent):
    #http://stackoverflow.com/questions/7835030/，可以从HTTP_X_FORWARDED_FOR提取真实IP，但是不太好用。	#经过对Openshift日志文件app-root/logs/python.log的分析，发现除了HTTP_X_FORWARDED_FOR外，HTTP_X_REAL_IP也可以获得真实的IP地址，而且更简单。    
    try:
	user_ip = environ['HTTP_X_REAL_IP']
    except KeyError:
	user_ip = environ['REMOTE_ADDR']
	
    url = "http://www.ip138.com/ips138.asp?ip=%s&action=2" % user_ip
    u = urllib2.urlopen(url)
    s = u.read()
    #Get IP Address Location
    result = re.findall(r'(<li>.*?</li>)',s)
    location = ""
    for i in result:
	location += i[4:-5]+"\n"
    #解析物理地址
    location = location.decode("gb2312").encode("utf-8")
    #保存文件
    if ostype == "Windows":
	logpath = "log.txt"
    else:
	logpath = "/var/lib/openshift/5749a7f30c1e66521c000168/app-root/runtime/repo/log.txt"    
    logfd = open(logpath,"a")
    logfd.write("用户 IP："+user_ip+"\n"+location+"提交内容："+sourcecontent+"\n\n")
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
