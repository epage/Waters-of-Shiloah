#!/usr/bin/env python

from __future__ import with_statement
from __future__ import division

import gobject
import logging


_moduleLogger = logging.getLogger(__name__)


class Stream(gobject.GObject):

	STATE_PLAY = "play"
	STATE_PAUSE = "pause"
	STATE_STOP = "stop"

	__gsignals__ = {
		'state-change' : (
			gobject.SIGNAL_RUN_LAST,
			gobject.TYPE_NONE,
			(gobject.TYPE_STRING, ),
		),
		'eof' : (
			gobject.SIGNAL_RUN_LAST,
			gobject.TYPE_NONE,
			(gobject.TYPE_STRING, ),
		),
		'error' : (
			gobject.SIGNAL_RUN_LAST,
			gobject.TYPE_NONE,
			(gobject.TYPE_PYOBJECT, gobject.TYPE_PYOBJECT),
		),
	}

	def __init__(self):
		gobject.GObject.__init__(self)

	@property
	def playing(self):
		return False

	@property
	def has_file(self):
		return False

	@property
	def state(self):
		return self.STATE_STOP

	def set_file(self, uri):
		self.emit("error", "Audio not supported on this platform", "")

	def play(self):
		self.emit("error", "Audio not supported on this platform", "")

	def pause(self):
		self.emit("error", "Audio not supported on this platform", "")

	def stop(self):
		self.emit("error", "Audio not supported on this platform", "")

	@property
	def elapsed(self):
		return 0

	@property
	def duration(self):
		return 0

	def seek_time(self, ns):
		self.emit("error", "Audio not supported on this platform", "")


if __name__ == "__main__":
	pass

