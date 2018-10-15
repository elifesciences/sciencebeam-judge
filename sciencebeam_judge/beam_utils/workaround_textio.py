import os

import apache_beam as beam

# The original WriteToText doesn't work with the experimental FnApiRunner
# because init_result is an empty side input
# This class is a workaround and shouldn't be necessary in the future


class WriteToText(beam.io.WriteToText, object):
    def __init__(self, *args, **kwargs):
        super(WriteToText, self).__init__(*args, **kwargs)
        self._original_open_writer = self._sink.open_writer
        self._sink.open_writer = self._open_writer
        self._file_opened = False

    def _open_writer(self, init_result, uid):
        if isinstance(init_result, beam.pvalue.EmptySideInput):
            # This happens with the current version of FnApiRunner (2.1.1)
            sink = self._sink
            file_path_prefix = sink.file_path_prefix.get()
            file_name_suffix = sink.file_name_suffix.get()
            filename = '{}.{}{}'.format(
                file_path_prefix, uid, file_name_suffix
            )
            try:
                beam.io.filesystems.FileSystems.mkdirs(
                    os.path.dirname(filename)
                )
            except IOError:
                pass
            return beam.io.filebasedsink.FileBasedSinkWriter(sink, filename)
        return self._original_open_writer(init_result, uid)
