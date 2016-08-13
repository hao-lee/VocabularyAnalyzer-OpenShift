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
	#tag转换之后的内容
	wordnet_tagged_list = []
	#将treebank类型的tag(如NN、NNP等),转为wordnet类型的tag(如wordnet.NOUN等)
	for treeback_tuple in treebank_tagged_list:
		wordnet_tuple = (treeback_tuple[0],get_wordnet_pos(treeback_tuple[1]))
		wordnet_tagged_list.append(wordnet_tuple)
	return wordnet_tagged_list	#单词<---->词性，一一对应

def lemmatizer(wordnet_tagged_list):
	wordnet_lemmatizer = WordNetLemmatizer()
	lemm_list = []	#存储还原后的单词列表
	for word_tag in wordnet_tagged_list:
		lemma = wordnet_lemmatizer.lemmatize(word_tag[0], word_tag[1])
		lemm_list.append(lemma)
	return set(lemm_list)

#wordnet_tagged_list = tokenizer("I’ normalized U.S. relations with Cuba ")
#print(lemmatizer(wordnet_tagged_list))