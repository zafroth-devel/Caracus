import sys

def import_module(name):
    __import__(name)
    return sys.modules[name]
#m = my_import("xml.etree.ElementTree") # returns ElementTree