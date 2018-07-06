from . import jats_xpath_functions
from . import tei_xpath_functions

def register_functions(ns=None):
  jats_xpath_functions.register_functions(ns)
  tei_xpath_functions.register_functions(ns)
