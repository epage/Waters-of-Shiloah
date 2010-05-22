import logging

import gobject

import util.misc as misc_utils
import stream
import stream_index
import call_monitor


_moduleLogger = logging.getLogger(__name__)


class Player(gobject.GObject):

	__gsignals__ = {
		'state_change' : (
			gobject.SIGNAL_RUN_LAST,
			gobject.TYPE_NONE,
			(gobject.TYPE_PYOBJECT, ),
		),
		'title_change' : (
			gobject.SIGNAL_RUN_LAST,
			gobject.TYPE_NONE,
			(gobject.TYPE_PYOBJECT, ),
		),
		'error' : (
			gobject.SIGNAL_RUN_LAST,
			gobject.TYPE_NONE,
			(gobject.TYPE_PYOBJECT, gobject.TYPE_PYOBJECT),
		),
	}

	STATE_PLAY = stream.GSTStream.STATE_PLAY
	STATE_PAUSE = stream.GSTStream.STATE_PAUSE
	STATE_STOP = stream.GSTStream.STATE_STOP

	def __init__(self, index):
		gobject.GObject.__init__(self)
		self._index = index
		self._node = None
		self._nextSearch = None

		self._calls = call_monitor.CallMonitor()
		self._calls.connect("call_start", self._on_call_start)

		self._stream = stream.GSTStream()
		self._stream.connect("state-change", self._on_stream_state)
		self._stream.connect("eof", self._on_stream_eof)
		self._stream.connect("error", self._on_stream_error)

	def set_piece_by_node(self, node):
		self._set_piece_by_node(node)

	@property
	def node(self):
		return self._node

	@property
	def title(self):
		if self._node is None:
			return ""
		return self._node.title

	@property
	def subtitle(self):
		if self._node is None:
			return ""
		return self._node.subtitle

	@property
	def can_navigate(self):
		if self._node is None:
			return False
		return self.node.can_navigate

	@property
	def state(self):
		return self._stream.state

	def play(self):
		_moduleLogger.info("play")
		self._stream.play()

		self._calls.start()

	def pause(self):
		_moduleLogger.info("pause")
		self._stream.pause()

	def stop(self):
		_moduleLogger.info("stop")
		self._stream.stop()
		self.set_piece_by_node(None)

		self._calls.stop()

	def back(self, forcePlay = False):
		_moduleLogger.info("back")
		assert self._nextSearch is None
		self._nextSearch = stream_index.AsyncWalker(stream_index.get_previous)
		self._nextSearch.start(
			self.node,
			lambda node: self._on_next_node(node, forcePlay),
			self._on_node_search_error
		)

	def next(self, forcePlay = False):
		_moduleLogger.info("next")
		assert self._nextSearch is None
		self._nextSearch = stream_index.AsyncWalker(stream_index.get_next)
		self._nextSearch.start(
			self.node,
			lambda node: self._on_next_node(node, forcePlay),
			self._on_node_search_error
		)

	def seek(self, percent):
		target = percent * self._stream.duration
		self._stream.seek_time(target)

	@property
	def percent_elapsed(self):
		percent = float(self._stream.elapsed) / float(self._stream.duration)
		return percent

	def _set_piece_by_node(self, node):
		assert node is None or node.is_leaf(), node
		if self._node is node:
			_moduleLogger.info("Already set to %r" % node)
			return
		self._node = node
		if self._node is not None:
			self._stream.set_file(self._node.uri)
		_moduleLogger.info("New node %r" % self._node)
		self.emit("title_change", self._node)

	@misc_utils.log_exception(_moduleLogger)
	def _on_next_node(self, node, forcePlay):
		self._nextSearch = None

		restart = self.state == self.STATE_PLAY
		self._set_piece_by_node(node)
		if restart or forcePlay:
			self.play()

	@misc_utils.log_exception(_moduleLogger)
	def _on_node_search_error(self, e):
		self._nextSearch = None
		self.emit("error", e, "")

	@misc_utils.log_exception(_moduleLogger)
	def _on_stream_state(self, s, state):
		_moduleLogger.info("State change %r" % state)
		self.emit("state_change", state)

	@misc_utils.log_exception(_moduleLogger)
	def _on_stream_eof(self, s, uri):
		_moduleLogger.info("EOF %s" % uri)
		self.next(forcePlay = True)

	@misc_utils.log_exception(_moduleLogger)
	def _on_stream_error(self, s, error, debug):
		_moduleLogger.info("Error %s %s" % (error, debug))
		self.emit("error", error, debug)

	@misc_utils.log_exception(_moduleLogger)
	def _on_call_start(self, monitor):
		_moduleLogger.info("Call in progress, pausing")
		self.pause()


gobject.type_register(Player)
