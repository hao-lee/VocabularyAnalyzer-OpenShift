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

#coca 20000词频表路径
if ostype == "Windows":
    corpuspath = "coca-20000.txt"
else:
    corpuspath = "/var/lib/openshift/5749a7f30c1e66521c000168/app-root/runtime/repo/coca-20000.txt"

#读取词频表
corpuslist = []
corpusfd = open(corpuspath, 'r')
for corpusword in corpusfd.readlines():
    corpuslist.append(corpusword.strip('\n'))
print len(corpuslist),"words have been read into memory."


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
<p>该在线工具可以对英文文本进行分析，提取出里面的高难度词汇。该工具是基于内置的词库来识别生词的,词库里面的单词是由专四、专八、托福、雅思、SAT、GRE的核心词汇表经过合并、排序、去重而来的，总计11567个单词，基本上全是比较难的词汇，但也不排除里面含有个别的四六级低阶词汇。</p>
<p>Tips:因为英语文本中的单词有很多都不是原形形态，而词库中都是原形，所以会有一些单词匹配不上，为了达到更好的识别效果需要将文本进行lemmatize（词形还原）。
请打开<a href=\"http://textanalysisonline.com/mbsp-word-lemmatize\" 
target=\"_blank\">词形还原工具</a>，将文本复制进去并点击\"MBSP Word 
Lemmatize\"，结果中右侧的文本就是还原后的。对还原后的文本使用本站工具进行检测会极大的提高识别率！</p>
<p>本工具同时内置了coca语料库中前20000个常用单词，会对提取出的单词按照常用程度排序。</p>
<form method="post" action=""> 
      <div style="text-align:center">
      <textarea name="inputtext" cols=130 rows=20>请在此粘贴文本</textarea>
      <p> 
         <input type="submit" value="请怒戳此按钮以便提交检测" style='font-size:30px' />
      </p>
      </div>
</form>
<hr>
<h2><B><font color="#0011ee">本工具由非营利英语学习论坛 EFL Club 出品，进入论坛请<a href=\"http://forum.eflclub.me\" target=\"_blank\">点此链接</a></font></B></h2>
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
	sourcecontent = post['inputtext'].value
	#保留用户请求日志
	save_log(environ,sourcecontent)	
	#调用分析器
	result = analyzer(sourcecontent);
	resultcontent = ""
	for word,ranking in result.iteritems():
	    resultcontent = resultcontent+word+"&nbsp"\
	        +str(ranking)+"<br>"
	#for word in resultlist:
	    #resultcontent = resultcontent+word+"<br>"
	response_body = resultpage_part1\
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

def analyzer(sourcecontent):
    #使用正则表达式，把单词提出出来，并都修改为小写格式
    sourcecontent = re.findall("\w+",str.lower(sourcecontent))
    #去除列表中的重复项，并排序
    sourcecontent = sorted(list(set(sourcecontent)))
    #去除含有数字和符号
    source_list = []
    for sourceword in sourcecontent:
	m = re.search("\d+",sourceword)
	n = re.search("\W+",sourceword)
	#if not m and  not n and len(i)>4:
	if not m and  not n:
	    source_list.append(sourceword)
    #print os.getcwd()
    if ostype == "Windows":
	dictpath = "total.txt"
    else:
	dictpath = "/var/lib/openshift/5749a7f30c1e66521c000168/app-root/runtime/repo/total.txt"
    dictfd = codecs.open(dictpath,"r","utf-8")
    dict_list = []#词典单词列表
    for dictword in dictfd.readlines():
	dict_list.append(dictword.strip('\n'))
    #print(dict_list)
    result = collections.OrderedDict()
    for word in source_list:#对每一个待查词汇
	if word in dict_list:#如果它在高阶词典里
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
    try:
	user_ip = environ['HTTP_X_FORWARDED_FOR'].split(',')[-1].strip()
    except KeyError:
	user_ip = environ['REMOTE_ADDR']
	
    url = "http://www.ip138.com/ips138.asp?ip=%s&action=2" % user_ip
    u = urllib2.urlopen(url)
    s = u.read()
    #Get IP Address Location
    result = re.findall(r'(<li>.*?</li>)',s)
    location = ""
    for i in result:
	location += i[4:-5]
    #解析物理地址
    location = location.decode("gb2312").encode("utf-8")
    #保存文件
    if ostype == "Windows":
	logpath = "log.txt"
    else:
	logpath = "/var/lib/openshift/5749a7f30c1e66521c000168/app-root/runtime/repo/log.txt"    
    logfd = open(logpath,"a")
    logfd.write("用户IP："+user_ip+" "+location+"\n"+"提交内容："+sourcecontent+"\n\n")
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
