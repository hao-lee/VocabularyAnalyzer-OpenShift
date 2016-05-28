# -*- coding: utf-8 -*-
import re
import string
#该程序用来测试文本分析功能是否可用
#输入文本
r = open("test.srt","r")
origincontent =r.read()
#使用正则表达式，把单词提出出来，并都修改为小写格式
lowercase = re.findall("\w+",str.lower(origincontent))
#去除列表中的重复项，并排序
processed = sorted(list(set(lowercase)))
#去除含有数字和符号，以及长度小于5的字符串
result_list = []
for item in processed:
	m = re.search("\d+",item)
	n = re.search("\W+",item)
	#if not m and  not n and len(i)>4:
	if not m and  not n:
		print(item)
		result_list.append(item)
r.close()