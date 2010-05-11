import logging

import gobject
import gtk


_moduleLogger = logging.getLogger(__name__)


class FakePlayer(gobject.GObject):

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

		self._title = gtk.Entry()
		self._title.connect("activate", self._title_change)

		self._playButton = gtk.RadioButton(label="Play")
		self._playButton.connect("clicked", self._state_change, "play")
		self._pauseButton = gtk.RadioButton(group=self._playButton, label="Pause")
		self._pauseButton.connect("clicked", self._state_change, "pause")
		self._stopButton = gtk.RadioButton(group=self._playButton, label="stop")
		self._stopButton.connect("clicked", self._state_change, "stop")

		self._canNavigate = gtk.CheckButton("Can Navigate?")
		self._canNavigate.connect("clicked", self._navigate_change)

		self._layout = gtk.VBox()
		self._layout.pack_start(self._title)
		self._layout.pack_start(self._playButton)
		self._layout.pack_start(self._pauseButton)
		self._layout.pack_start(self._stopButton)
		self._layout.pack_start(self._canNavigate)

		self._state = "stop"

	@property
	def toplevel(self):
		return self._layout

	@property
	def node(self):
		return None

	@property
	def title(self):
		return self._title.get_text()

	@property
	def can_navigate(self):
		return self._canNavigate.get_active()

	@property
	def state(self):
		return self._state

	def _state_change(self, widget, state):
		_moduleLogger.info("User changed state")
		self.emit("state_change", state)
		self._state = state

	def _navigate_change(self, widget):
		_moduleLogger.info("User changed nav")
		self.emit("navigate_change", self._canNavigate.get_active())

	def _title_change(self, widget):
		_moduleLogger.info("User changed title")
		self.emit("title_change", self._title.get_text())

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


gobject.type_register(FakePlayer)
