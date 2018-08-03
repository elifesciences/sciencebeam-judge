import logging

from six import text_type, string_types


LOGGER = logging.getLogger(__name__)


# functions may move to sciencebeam-util in the future


IGNORE_MARKER = '_ignore_'
IGNORE_MARKER_WITH_SPACE = ' ' + IGNORE_MARKER + ' '


def _default_exclude_fn(node):
  tag = node.tag
  result = not isinstance(tag, string_types)
  LOGGER.debug('_default_exclude_fn: node.tag=%s, result=%s', tag, result)
  return result


def _to_exclude_fn(exclude):
  if exclude is None:
    return _default_exclude_fn
  if isinstance(exclude, (set, list)):
    return lambda x: x in exclude
  return exclude


def _iter_text_content_and_exclude(node, exclude_fn, exclude_placeholder=''):
  if node.text is not None:
    yield node.text

  for c in node.iterchildren():
    if exclude_fn is not None and exclude_fn(c):
      LOGGER.debug('excluded child: %s (placeholder: %s)', c, exclude_placeholder)
      yield exclude_placeholder
    else:
      for t in _get_text_content_and_exclude(c, exclude_fn, exclude_placeholder):
        yield t
    if c.tail is not None:
      yield c.tail


def _get_text_content_and_exclude(node, exclude, exclude_placeholder=''):
  return ''.join([
    c for c in _iter_text_content_and_exclude(
      node,
      exclude_fn=_to_exclude_fn(exclude),
      exclude_placeholder=exclude_placeholder
    )
  ])


def get_text_content(node, exclude=None):
  if node is None:
    return ''
  if not hasattr(node, 'text'):
    return text_type(node)
  return _get_text_content_and_exclude(node, exclude=exclude)


def get_text_content_list(nodes, **kwargs):
  return [get_text_content(node, **kwargs) for node in nodes]


def get_text_content_and_ignore_children(e, children_to_ignore):
  # Note: this is similar to get_text_content with exclude keyword parameter
  #   but also provides an ignore marker (should be merged)
  if children_to_ignore is None or len(children_to_ignore) == 0:
    return get_text_content(e)
  if e.text is not None:
    return ''.join(e.xpath('text()'))
  return "".join([
    get_text_content_and_ignore_children(c, children_to_ignore)
    if c not in children_to_ignore else IGNORE_MARKER_WITH_SPACE
    for c in e
  ])
