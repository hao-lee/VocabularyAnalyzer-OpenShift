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
Lemmatize\"，结果中右侧的文本就是还原后的。将还原后的文本保存为文本文件（txt等），然后再使用本站工具进行检测会极大的提高识别率！</p>
<p></p>
<form method="post" action=""> 
      <div style="text-align:center">
      <textarea name="inputtext" cols=130 rows=20>请在此粘贴文本</textarea>
      <p> 
         <input type="submit" value="请怒戳此按钮以便提交检测" style='font-size:30px' />
      </p>
      </div>
</form>
<hr>
<p>页面不是很好看，将就着用吧，等我忙完毕设再完善完善。</p>
<p><B><font color="#0011ee">本工具由非营利英语学习论坛 EFL Club 出品，进入论坛请<a href=\"http://forum.eflclub.me\" target=\"_blank\">点此链接</a></font></B></p>
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
<p>以下单词被认为难度较大</p>
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
	resultlist = analyzer(sourcecontent);
	resultcontent = ""
	for word in resultlist:
	    resultcontent = resultcontent+word+"<br>"
	response_body = resultpage_part1\
	    + resultcontent\
	    +"<br><a href=\"/VocabularyAnalyzer\">Back</a>"\
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

    dictfd = codecs.open("total.txt","r","utf-8")
    dict_list = ["abandon"]
    for dictword in dictfd.readlines():
	dict_list.append(dictword.strip('\n'))
    #print(dict_list)
    result_list = []
    for word in source_list:
	if word in dict_list:
	    #print(word)
	    result_list.append(word)
    return result_list

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
