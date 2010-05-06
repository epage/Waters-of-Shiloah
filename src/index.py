import logging

from util import go_utils
import backend


_moduleLogger = logging.getLogger(__name__)


class AudioIndex(object):

	def __init__(self):
		self._backend = backend.Backend()
		self._indexing = go_utils.AsyncPool()

	def start(self):
		self._indexing.start()

	def stop(self):
		self._indexing.stop()

	def download(self, func, on_success, on_error, *args, **kwds):
		self._indexing.clear_tasks()
		self._indexing.add_task(
			getattr(self._backend, func),
			args,
			kwds,
			on_success,
			on_error,
		)
