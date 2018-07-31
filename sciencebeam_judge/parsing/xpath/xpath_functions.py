from . import generic_xpath_functions
from . import jats_xpath_functions
from . import tei_xpath_functions

def register_functions(ns=None):
  generic_xpath_functions.register_functions(ns)
  jats_xpath_functions.register_functions(ns)
  tei_xpath_functions.register_functions(ns)
