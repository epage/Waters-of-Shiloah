import logging

import gtk

import gtk_toolbox
import hildonize
import util.misc as misc_utils


_moduleLogger = logging.getLogger(__name__)


class PlayControl(object):

	def __init__(self, player, store):
		self._isPortrait = True

		self._store = store

		self._player = player
		self._player.connect("state-change", self._on_player_state_change)
		self._player.connect("title-change", self._on_player_nav_change)

		img = store.get_image_from_store(store.STORE_LOOKUP["prev"])
		self._back = gtk.Button()
		self._back.set_image(img)
		self._back.connect("clicked", self._on_back_clicked)

		img = store.get_image_from_store(store.STORE_LOOKUP["stop"])
		self._stop = gtk.Button()
		self._stop.set_image(img)
		self._stop.connect("clicked", self._on_stop_clicked)

		img = store.get_image_from_store(store.STORE_LOOKUP["pause"])
		self._pause = gtk.Button()
		self._pause.set_image(img)
		self._pause.connect("clicked", self._on_pause_clicked)

		img = store.get_image_from_store(store.STORE_LOOKUP["play"])
		self._play = gtk.Button()
		self._play.set_image(img)
		self._play.connect("clicked", self._on_play_clicked)

		img = store.get_image_from_store(store.STORE_LOOKUP["next"])
		self._next = gtk.Button()
		self._next.set_image(img)
		self._next.connect("clicked", self._on_next_clicked)

		self._controls = gtk.HBox()
		self._controls.pack_start(self._back)
		self._controls.pack_start(self._stop)
		self._controls.pack_start(self._pause)
		self._controls.pack_start(self._play)
		self._controls.pack_start(self._next)

		self._layout = gtk.VBox()
		self._layout.pack_start(self._controls)

	def refresh(self):
		if not self._player.title:
			self.toplevel.hide()
		self._set_navigate(self._player.can_navigate)
		self._set_state(self._player.state)

	@property
	def toplevel(self):
		return self._layout

	def set_orientation(self, orientation):
		if orientation == gtk.ORIENTATION_VERTICAL:
			if self._isPortrait:
				return
			self._isPortrait = True

			self._controls.remove(self._back)
			self._controls.remove(self._stop)
			self._controls.remove(self._pause)
			self._controls.remove(self._play)
			self._controls.remove(self._next)
			self._layout.remove(self._controls)

			self._controls = gtk.HBox()
			self._controls.pack_start(self._back)
			self._controls.pack_start(self._stop)
			self._controls.pack_start(self._pause)
			self._controls.pack_start(self._play)
			self._controls.pack_start(self._next)
			self._layout.pack_start(self._controls)
		elif orientation == gtk.ORIENTATION_HORIZONTAL:
			if not self._isPortrait:
				return
			self._isPortrait = False

			self._controls.remove(self._back)
			self._controls.remove(self._stop)
			self._controls.remove(self._pause)
			self._controls.remove(self._play)
			self._controls.remove(self._next)
			self._layout.remove(self._controls)

			self._controls = gtk.VBox()
			self._controls.pack_start(self._back)
			self._controls.pack_start(self._stop)
			self._controls.pack_start(self._pause)
			self._controls.pack_start(self._play)
			self._controls.pack_start(self._next)
			self._layout.pack_start(self._controls)
		else:
			raise NotImplementedError(orientation)

	def _set_navigate(self, canNavigate):
		if canNavigate:
			self._back.show()
			self._next.show()
		else:
			self._back.hide()
			self._next.hide()

	def _set_state(self, newState):
		if newState == "play":
			self._pause.show()
			self._play.hide()
			self.toplevel.show()
		elif newState == "pause":
			self._pause.hide()
			self._play.show()
			self.toplevel.show()
		elif newState == "stop":
			self._pause.hide()
			self._play.show()
			self.toplevel.hide()

	@misc_utils.log_exception(_moduleLogger)
	def _on_player_state_change(self, player, newState):
		self._set_state(newState)

	@misc_utils.log_exception(_moduleLogger)
	def _on_player_nav_change(self, player, newState):
		self._set_navigate(player.can_navigate)

	@misc_utils.log_exception(_moduleLogger)
	def _on_back_clicked(self, *args):
		self._player.back()

		parent = gtk_toolbox.find_parent_window(self._layout)
		hildonize.show_information_banner(parent, self._player.title)

	@misc_utils.log_exception(_moduleLogger)
	def _on_stop_clicked(self, *args):
		self._pause.hide()
		self._play.show()
		self._player.stop()

	@misc_utils.log_exception(_moduleLogger)
	def _on_pause_clicked(self, *args):
		self._pause.show()
		self._play.hide()
		self._player.pause()

	@misc_utils.log_exception(_moduleLogger)
	def _on_play_clicked(self, *args):
		self._pause.hide()
		self._play.show()
		self._player.play()

	@misc_utils.log_exception(_moduleLogger)
	def _on_next_clicked(self, *args):
		self._player.next()

		parent = gtk_toolbox.find_parent_window(self._layout)
		hildonize.show_information_banner(parent, self._player.title)
