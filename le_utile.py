#!/usr/bin/env python
# -*- coding: utf-8 -*-

#Copyright (c) 2014, Le Tuan Anh <tuananh.ke@gmail.com>

#Permission is hereby granted, free of charge, to any person obtaining a copy
#of this software and associated documentation files (the "Software"), to deal
#in the Software without restriction, including without limitation the rights
#to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
#copies of the Software, and to permit persons to whom the Software is
#furnished to do so, subject to the following conditions:

#The above copyright notice and this permission notice shall be included in
#all copies or substantial portions of the Software.

#THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
#AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
#LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
#OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
#THE SOFTWARE.

import codecs
import sys

def jilog(msg):
    sys.stderr.write((u"%s" % unicode(msg)).encode("ascii","ignore"))
    try:
        with codecs.open("debug.txt", "a", encoding='utf-8') as logfile:
            logfile.write(u"%s\n" % unicode(msg))
    except Exception as ex:
        sys.stderr.write(str(ex))
        pass

import time
class Timer:
    def __init__(self):
        self.start_time = time.time()
        self.end_time = time.time()
    def start(self, task_note=''):
		if task_note:
			jilog(u"[%s]\n" % (unicode(task_note),))
		self.start_time = time.time()
		return self
			
    def stop(self):
        self.end_time = time.time()
        return self
    def __str__(self):
        return "Execution time: %.2f sec(s)" % (self.end_time - self.start_time)
    def log(self, task_note = ''):
        jilog(u"%s - Note=[%s]\n" % (self, unicode(task_note)))
        return self
    def end(self, task_note=''):
            self.stop().log(task_note)

class Counter:
	def __init__(self):
		self.count_map = {}
    
	def __getitem__(self, key):
		if not self.count_map.has_key(key):
			self.count_map[key] = 0
		return self.count_map[key]
	
	def __setitem__(self, key, value):
		self.count_map[key] = value
    
	def count(self, key):
		self[key] += 1
    
	def summarise(self):
		for k in self.count_map.keys():
			print("%s: %d" % (k, self.count_map[k]))

class StringTool:
	@staticmethod
	def strip(a_str):
		return a_str.strip() if a_str else ''
	
	@staticmethod
	def to_str(a_str):
		return unicode(a_str) if a_str else ''

def main():
	print("This is an utility module, not an application.")
	pass

if __name__ == "__main__":
	main()
