import logging

import apache_beam as beam


def get_logger():
    return logging.getLogger(__name__)


def Spy(f):
    def spy_wrapper(x):
        f(x)
        return x
    return spy_wrapper


def MapSpy(f):
    return beam.Map(Spy(f))


def MapOrLog(fn):
    def wrapper(x):
        try:
            yield fn(x)
        except Exception as e:  # pylint: disable=broad-except
            get_logger().warning('caucht exception (ignoring item): %s, input: %.100s...', e, x)
    return beam.FlatMap(wrapper)


LEVEL_MAP = {
    'info': logging.INFO,
    'debug': logging.DEBUG
}


def _default_log_value_fn(x):
    return x


class TransformAndLog(beam.PTransform):
    def __init__(self, transform, log_fn=None, log_prefix='', log_value_fn=None, log_level='info'):
        super().__init__()
        self.transform = transform
        if log_fn is None:
            if log_value_fn is None:
                log_value_fn = _default_log_value_fn
            log_level = LEVEL_MAP.get(log_level, log_level)
            self.log_fn = lambda x: get_logger().log(
                log_level, '%s%.50s...', log_prefix, log_value_fn(x)
            )
        else:
            self.log_fn = log_fn

    def expand(self, pcoll):  # pylint: disable=arguments-differ
        return (
            pcoll |
            self.transform |
            "Log" >> MapSpy(self.log_fn)
        )
