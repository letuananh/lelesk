#!/usr/bin/env python
# -*- coding: utf-8 -*-

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
    def start(self):
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

def main():
	print("This is an utility module, not an application.")
	pass

if __name__ == "__main__":
	main()
