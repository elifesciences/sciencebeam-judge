from sciencebeam_judge.evaluation_utils import (
  comma_separated_str_to_list
)


class TestCommaSeparatedStrToList(object):
  def test_should_parse_empty_str_as_empty_list(self):
    assert comma_separated_str_to_list('') == []

  def test_should_parse_single_item_str_as_single_item_list(self):
    assert comma_separated_str_to_list('abc') == ['abc']

  def test_should_parse_multiple_item_str(self):
    assert comma_separated_str_to_list('abc,xyz,123') == ['abc', 'xyz', '123']

  def test_should_strip_space_around_items(self):
    assert comma_separated_str_to_list(' abc , xyz , 123 ') == ['abc', 'xyz', '123']
