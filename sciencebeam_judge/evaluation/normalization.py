# -*- coding: utf-8 -*-

import re

from six import unichr  # pylint: disable=redefined-builtin


FULL_PUNCTUATIONS = u"([ •*,:;?.!/)-−–\"“”‘’'`$]*\u2666\u2665\u2663\u2660\u00A0"
WHITE_SPACE = u" \t\n\r\u00A0"
NBSP = unichr(160)

FULL_PUNCTUATION_AND_WHITESPACE_REGEX = re.compile(
    u'[{}]'.format(re.escape(FULL_PUNCTUATIONS + WHITE_SPACE)))

WHITESPACE_REGEX = re.compile(r'\s+')


def normalize_whitespace(s):
    return WHITESPACE_REGEX.sub(' ', s).replace(NBSP, ' ')


def normalize_string(s, convert_to_lower=False):
    s = normalize_whitespace(s)
    if convert_to_lower:
        s = s.lower()
    return s


def strip_punctuation_and_whitespace(s):
    return FULL_PUNCTUATION_AND_WHITESPACE_REGEX.sub('', s)
