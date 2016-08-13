# -*- coding: utf-8 -*-
#!/usr/bin/python
import nltk
from nltk.corpus import wordnet
import collections
from collections import OrderedDict
from nltk.stem import WordNetLemmatizer

def get_wordnet_pos(treebank_tag):
	if treebank_tag.startswith('J'):
		return wordnet.ADJ
	elif treebank_tag.startswith('V'):
		return wordnet.VERB
	elif treebank_tag.startswith('N'):
		return wordnet.NOUN
	elif treebank_tag.startswith('R'):
		return wordnet.ADV
	else:
		return wordnet.NOUN	#默认当作名词处理

def tokenizer(sourcestring):
	#转为小写（不转似乎也没影响）
	sourcestring = str.lower(sourcestring)
	text = nltk.word_tokenize(sourcestring)	#分词
	treebank_tagged_list = nltk.pos_tag(text)	#打标签
	#tag转换之后的内容，以字典来存储更方便
	wordnet_tagged_dict = {}
	#将treebank类型的tag(如NN、NNP等),转为wordnet类型的tag(如wordnet.NOUN等)
	for one_tuple in treebank_tagged_list:
		wordnet_tagged_dict[one_tuple[0]] = \
		        get_wordnet_pos(one_tuple[1])
	return wordnet_tagged_dict	#单词<---->词性，一一对应

def lemmatizer(wordnet_tagged_dict):
	wordnet_lemmatizer = WordNetLemmatizer()
	lemm_list = []	#存储还原后的单词列表
	for word,tag in wordnet_tagged_dict.items():
		print (word,tag)
		lemma  = wordnet_lemmatizer.lemmatize(word, tag)
		lemm_list.append(lemma)
	print (lemm_list)
	return lemm_list

#wordnet_tagged_dict = tokenizer("I’ normalized U.S. relations with Cuba ")
#lemmatizer(wordnet_tagged_dict)