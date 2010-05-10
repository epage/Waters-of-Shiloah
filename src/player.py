import logging

import gobject


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
	}

	def __init__(self, index):
		gobject.GObject.__init__(self)
		self._index = index
		self._node = None
		self._state = "play"

	def set_piece_by_node(self, node):
		assert node.is_leaf() or node is None
		if self._node is node:
			return
		self._node = node
		self.emit("title_change", self._state)

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
		return self._state

	def play(self):
		if self._state == "play":
			return
		self._state = "play"
		self.emit("state_change", self._state)
		_moduleLogger.info("play")

	def pause(self):
		if self._state == "pause":
			return
		self._state = "pause"
		self.emit("state_change", self._state)
		_moduleLogger.info("pause")

	def stop(self):
		if self._state == "stop":
			return
		self._state = "stop"
		self.set_piece_by_node(None)
		self.emit("state_change", self._state)
		_moduleLogger.info("stop")

	def back(self):
		_moduleLogger.info("back")

	def next(self):
		_moduleLogger.info("next")


gobject.type_register(Player)
