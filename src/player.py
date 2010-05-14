import logging

import gobject

import util.misc as misc_utils
import stream


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

		self._stream = stream.GSTStream()
		self._stream.connect("state-change", self._on_stream_state)
		self._stream.connect("eof", self._on_stream_eof)
		self._stream.connect("error", self._on_stream_error)

	def set_piece_by_node(self, node):
		assert node is None or node.is_leaf(), node
		if self._node is node:
			return
		self._node = node
		if self._node is not None:
			self._stream.set_file(self._node.uri)
		_moduleLogger.info("New node %r" % self._node)
		self.emit("title_change", self._node)

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

	def pause(self):
		_moduleLogger.info("pause")
		self._stream.pause()

	def stop(self):
		_moduleLogger.info("stop")
		self._stream.stop()
		self.set_piece_by_node(None)

	def back(self):
		_moduleLogger.info("back")

	def next(self):
		_moduleLogger.info("next")

	@misc_utils.log_exception(_moduleLogger)
	def _on_stream_state(self, s, state):
		_moduleLogger.info("State change %r" % state)
		self.emit("state_change", state)

	@misc_utils.log_exception(_moduleLogger)
	def _on_stream_eof(self, s, uri):
		_moduleLogger.info("EOF %s" % uri)
		self.next()

	@misc_utils.log_exception(_moduleLogger)
	def _on_stream_error(self, s, error, debug):
		_moduleLogger.info("Error %s %s" % (error, debug))
		self.emit("error", error, debug)


gobject.type_register(Player)
