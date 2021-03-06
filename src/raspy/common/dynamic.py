#!/usr/bin/python
# -*- coding: utf-8 -*-

import new

def importCode(code, name, add_to_sys_modules=False):
   # code can be any object containing code: a string, a file object, or
   # a compiled code object.  Returns a new module object initialized
   # by dynamically importing the given code, and optionally adds it
   # to sys.modules under the given name.
   #
    module = new.module(name)
    if add_to_sys_modules:
        import sys
        sys.modules[name] = module
    exec code in module.__dict__
    return module

code = """
def testFunc( ):
   print "spam!"
class testClass(object):
   def testMethod(self):
      print "eggs!"
"""
m = importCode(code, "test")
m.testFunc()
o = m.testClass()
o.testMethod()
