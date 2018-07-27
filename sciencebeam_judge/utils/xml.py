import logging

from six import text_type

from sciencebeam_gym.utils.xml import get_text_content as _get_text_content


LOGGER = logging.getLogger(__name__)


# functions may move to sciencebeam-util in the future


IGNORE_MARKER = '_ignore_'
IGNORE_MARKER_WITH_SPACE = ' ' + IGNORE_MARKER + ' '


def get_text_content(node, exclude=None):
  if node is None:
    return ''
  try:
    return _get_text_content(node, exclude=exclude)
  except AttributeError:
    return text_type(node)


def get_text_content_or_blank(node):
  LOGGER.debug('node: %s', node)
  return get_text_content(node) if node is not None else ''


def get_full_text(e):
  return get_text_content(e)


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
