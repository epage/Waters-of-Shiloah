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
		'navigate_change' : (
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

	def __init__(self):
		gobject.GObject.__init__(self)

	@property
	def title(self):
		return ""

	@property
	def can_navigate(self):
		return True

	@property
	def state(self):
		return "play"

	@property
	def background(self):
		return "night_temple_background"

	def play(self):
		_moduleLogger.info("play")

	def pause(self):
		_moduleLogger.info("pause")

	def stop(self):
		_moduleLogger.info("stop")

	def back(self):
		_moduleLogger.info("back")

	def next(self):
		_moduleLogger.info("next")


gobject.type_register(Player)
