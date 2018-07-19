from abc import ABCMeta, abstractmethod

from six import with_metaclass

class ScoringType(object, with_metaclass(ABCMeta)):
  @abstractmethod
  def score(self, expected, actual, include_values=False, measures=None, convert_to_lower=False):
    pass
