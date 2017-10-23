# -*- coding: utf-8 -*-
from __future__ import division

import re
from difflib import SequenceMatcher

from six import raise_from, string_types
from six.moves.configparser import ConfigParser

from lxml import etree as ET
import editdistance

IGNORE_MARKER = '_ignore_'
IGNORE_MARKER_WITH_SPACE = ' ' + IGNORE_MARKER + ' '

def get_full_text(e):
  return "".join(e.itertext())

def get_full_text_ignore_children(e, children_to_ignore):
  if children_to_ignore is None or len(children_to_ignore) == 0:
    return get_full_text(e)
  if e.text is not None:
    return ''.join(e.xpath('text()'))
  return "".join([
    get_full_text_ignore_children(c, children_to_ignore)
    if c not in children_to_ignore else IGNORE_MARKER_WITH_SPACE
    for c in e
  ])

def parse_xml_mapping(xml_mapping_filename_or_fp):
  config = ConfigParser()
  if isinstance(xml_mapping_filename_or_fp, string_types):
    config.read(xml_mapping_filename_or_fp)
  else:
    config.readfp(xml_mapping_filename_or_fp)
  return {
    k: dict(config.items(k))
    for k in config.sections()
  }

def strip_namespace(it):
  for _, el in it:
    if '}' in el.tag:
      el.tag = el.tag.split('}', 1)[1]  # strip all namespaces
  return it

def parse_ignore_namespace(source):
  try:
    return strip_namespace(ET.iterparse(source)).root
  except ET.XMLSyntaxError as e:
    raise_from(RuntimeError('failed to process {}'.format(source)), e)

def parse_xml(source, xml_mapping, fields=None):
  root = parse_ignore_namespace(source)
  if not root.tag in xml_mapping:
    raise Exception("unrecognised tag: {} (available: {})".format(root.tag, xml_mapping.sections()))
  mapping = xml_mapping[root.tag]
  field_names = [
    k
    for k in mapping.keys()
    if (fields is None or k in fields) and '.ignore' not in k
  ]
  result = {
    k: [
      get_full_text_ignore_children(
        e,
        e.xpath(mapping[k + '.ignore']) if k + '.ignore' in mapping else None
      ).strip()
      for e in root.xpath(mapping[k])
    ]
    for k in field_names
  }
  return result

FULL_PUNCTUATIONS = u"([ •*,:;?.!/)-−–\"“”‘’'`$]*\u2666\u2665\u2663\u2660\u00A0"
WHITE_SPACE = u" \t\n\r\u00A0"
NBSP = unichr(160)

FULL_PUNCTUATION_AND_WHITESPACE_REGEX = re.compile(
  u'[{}]'.format(re.escape(FULL_PUNCTUATIONS + WHITE_SPACE)))

WHITESPACE_REGEX = re.compile(r'\s+')

def normalize_whitespace(s):
  return WHITESPACE_REGEX.sub(' ', s).replace(NBSP, ' ')

def strip_punctuation_and_whitespace(s):
  return FULL_PUNCTUATION_AND_WHITESPACE_REGEX.sub('', s)

def exact_score(expected, actual):
  return 1 if expected == actual else 0

def levenshtein_score(expected, actual):
  if len(expected) == 0 and len(actual) == 0:
    return 1
  return 1 - (editdistance.eval(expected, actual) / max(len(expected), len(actual)))

def ratcliff_obershelp_score(expected, actual):
  return SequenceMatcher(None, expected, actual).ratio()

def score_obj(expected, actual, value_f, threshold=1, include_values=False):
  binary_expected = 1 if len(expected) > 0 else 0
  # actual will be a false positive (1) if it is populated but expected is not,
  # otherwise it will be positive if it meets the threshold
  value = value_f(expected, actual)
  binary_actual = (
    1
    if len(actual) > 0 and (binary_expected == 0 or (binary_expected == 1 and value >= threshold))
    else 0
  )
  tp = 1 if len(actual) > 0 and len(expected) > 0 and value >= threshold else 0
  tn = 1 if len(actual) == 0 and len(expected) == 0 else 0
  fp = 1 if not tp and len(actual) > 0 else 0
  fn = 1 if not tn and len(actual) == 0 else 0
  d = {
    'expected_something': len(expected) > 0,
    'actual_something': len(actual) > 0,
    'score': value,
    'true_positive': tp,
    'true_negative': tn,
    'false_positive': fp,
    'false_negative': fn,
    'binary_expected': binary_expected,
    'binary_actual': binary_actual
  }
  if include_values:
    d['expected'] = expected
    d['actual'] = actual
  return d

def score_list(expected, actual, include_values=False):
  # sep = '\n'
  sep = ''
  expected_str = normalize_whitespace(sep.join(expected)).lower()
  actual_str = normalize_whitespace(sep.join(actual)).lower()
  return {
    'exact': score_obj(
      expected_str,
      actual_str,
      exact_score,
      include_values=include_values
    ),
    'soft': score_obj(
      strip_punctuation_and_whitespace(expected_str),
      strip_punctuation_and_whitespace(actual_str),
      exact_score,
      include_values=include_values
    ),
    'levenshtein': score_obj(
      expected_str,
      actual_str,
      levenshtein_score,
      0.8,
      include_values=include_values
    ),
    'ratcliff_obershelp': score_obj(
      expected_str,
      actual_str,
      ratcliff_obershelp_score,
      0.95,
      include_values=include_values
    )
  }

def score_results(expected, actual, include_values=False):
  return {
    k: score_list(expected[k], actual[k], include_values=include_values)
    for k in expected.keys()
  }

def comma_separated_str_to_list(s):
  s = s.strip()
  if len(s) == 0:
    return []
  return [item.strip() for item in s.split(',')]
