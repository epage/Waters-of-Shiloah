import logging

import gobject
import gtk

import gtk_toolbox
import hildonize
import util.go_utils as go_utils
import util.misc as misc_utils

import presenter


_moduleLogger = logging.getLogger(__name__)


class NavControl(gobject.GObject, go_utils.AutoSignal):


	__gsignals__ = {
		'home' : (
			gobject.SIGNAL_RUN_LAST,
			gobject.TYPE_NONE,
			(),
		),
		'jump-to' : (
			gobject.SIGNAL_RUN_LAST,
			gobject.TYPE_NONE,
			(gobject.TYPE_PYOBJECT, ),
		),
	}

	def __init__(self, player, store):
		gobject.GObject.__init__(self)

		self._store = store

		self._controlButton = store.get_image_from_store(store.STORE_LOOKUP["play"])

		self._controlBox = presenter.NavigationBox()
		self._controlBox.toplevel.add(self._controlButton)
		self._controlBox.connect("action", self._on_nav_action)
		self._controlBox.connect("navigating", self._on_navigating)

		self._titleButton = gtk.Label()

		self._displayBox = presenter.NavigationBox()
		self._displayBox.toplevel.add(self._titleButton)
		self._displayBox.connect("action", self._on_nav_action)
		self._displayBox.connect("navigating", self._on_navigating)

		self._layout = gtk.HBox()
		go_utils.AutoSignal.__init__(self, self.toplevel)
		self._layout.pack_start(self._controlBox.toplevel, False, False)
		self._layout.pack_start(self._displayBox.toplevel, True, True)
		self._player = player
		self.connect_auto(self._player, "state-change", self._on_player_state_change)
		self.connect_auto(self._player, "title-change", self._on_player_title_change)
		self._titleButton.set_label(self._player.title)

	def refresh(self):
		self._titleButton.set_label(self._player.title)
		self._set_context(self._player.state)

	def _set_context(self, state):
		if state == self._player.STATE_PLAY:
			stateImage = self._store.STORE_LOOKUP["pause"]
			self._store.set_image_from_store(self._controlButton, stateImage)
			self.toplevel.show()
		elif state == self._player.STATE_PAUSE:
			stateImage = self._store.STORE_LOOKUP["play"]
			self._store.set_image_from_store(self._controlButton, stateImage)
			self.toplevel.show()
		elif state == self._player.STATE_STOP:
			self._titleButton.set_label("")
			self.toplevel.hide()
		else:
			_moduleLogger.info("Unhandled player state %s" % state)
			stateImage = self._store.STORE_LOOKUP["pause"]
			self._store.set_image_from_store(self._controlButton, stateImage)

	@property
	def toplevel(self):
		return self._layout

	def set_orientation(self, orientation):
		pass

	@misc_utils.log_exception(_moduleLogger)
	def _on_player_state_change(self, player, newState):
		if self._controlBox.is_active() or self._displayBox.is_active():
			return

		self._set_context(newState)

	@misc_utils.log_exception(_moduleLogger)
	def _on_player_title_change(self, player, node):
		_moduleLogger.info("Title change: %s" % self._player.title)
		self._titleButton.set_label(self._player.title)

	@misc_utils.log_exception(_moduleLogger)
	def _on_navigating(self, widget, navState):
		if navState == "down":
			imageName = "home"
		elif navState == "clicking":
			if widget is self._controlBox:
				if self._player.state == self._player.STATE_PLAY:
					imageName = "pause_pressed"
				else:
					imageName = "play_pressed"
			else:
				if self._player.state == self._player.STATE_PLAY:
					imageName = "pause"
				else:
					imageName = "play"
		elif self._player.can_navigate:
			if navState == "up":
				imageName = "play"
			elif navState == "left":
				imageName = "next"
			elif navState == "right":
				imageName = "prev"
		else:
			if self._player.state == self._player.STATE_PLAY:
				imageName = "pause"
			else:
				imageName = "play"

		imagePath = self._store.STORE_LOOKUP[imageName]
		self._store.set_image_from_store(self._controlButton, imagePath)

	@misc_utils.log_exception(_moduleLogger)
	def _on_nav_action(self, widget, navState):
		self._set_context(self._player.state)

		if navState == "clicking":
			if widget is self._controlBox:
				if self._player.state == self._player.STATE_PLAY:
					self._player.pause()
				else:
					self._player.play()
			elif widget is self._displayBox:
				self.emit("jump-to", self._player.node)
			else:
				raise NotImplementedError()
		elif navState == "down":
			self.emit("home")
		elif navState == "up":
			pass
		elif navState == "left":
			self._player.next()
		elif navState == "right":
			self._player.back()


gobject.type_register(NavControl)
