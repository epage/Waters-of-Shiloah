from util import go_utils
import backend


class AudioIndex(object):

	def __init__(self):
		self._backend = backend.Backend()
		self._indexing = go_utils.AsyncPool()

	def start(self):
		self._indexing.start()

	def stop(self):
		self._indexing.stop()

	def download_radio(self, on_success, on_error, *ids):
		self._indexing.clear_tasks()
		if ids:
			assert len(ids) == 1
			self._indexing.add_task(
				self._backend.get_radio_channel_programming,
				(ids[0], ),
				{},
				on_success,
				on_error,
			)
		else:
			self._indexing.add_task(
				self._backend.get_radio_channels,
				(),
				{},
				on_success,
				on_error,
			)
