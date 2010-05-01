import logging

import gtk

import util.misc as misc_utils


_moduleLogger = logging.getLogger(__name__)


class PlayControl(object):

	def __init__(self, player, store):
		self._store = store

		self._player = player
		self._player.connect("state-change", self._on_player_state_change)
		self._player.connect("navigate-change", self._on_player_nav_change)

		img = store.get_image_from_store("prev.png")
		self._back = gtk.Button()
		self._back.set_image(img)
		self._back.connect("clicked", self._on_back_clicked)

		img = store.get_image_from_store("stop.png")
		self._stop = gtk.Button()
		self._stop.set_image(img)
		self._stop.connect("clicked", self._on_stop_clicked)

		img = store.get_image_from_store("pause.png")
		self._pause = gtk.Button()
		self._pause.set_image(img)
		self._pause.connect("clicked", self._on_pause_clicked)

		img = store.get_image_from_store("play.png")
		self._play = gtk.Button()
		self._play.set_image(img)
		self._play.connect("clicked", self._on_play_clicked)

		img = store.get_image_from_store("next.png")
		self._next = gtk.Button()
		self._next.set_image(img)
		self._next.connect("clicked", self._on_next_clicked)

		self._controls = gtk.HBox()
		self._controls.pack_start(self._back)
		self._controls.pack_start(self._stop)
		self._controls.pack_start(self._pause)
		self._controls.pack_start(self._play)
		self._controls.pack_start(self._next)

	@property
	def toplevel(self):
		return self._controls

	@misc_utils.log_exception(_moduleLogger)
	def _on_player_state_change(self, player, newState):
		if newState == "play":
			self._pause.show()
			self._play.hide()
		elif newState == "pause":
			self._pause.hide()
			self._play.show()
		elif newState == "stop":
			self._pause.hide()
			self._play.show()

		if self._player.can_navigate:
			self._back.show()
			self._next.show()
		else:
			self._back.hide()
			self._next.hide()

	@misc_utils.log_exception(_moduleLogger)
	def _on_player_nav_change(self, player, canNavigate):
		if canNavigate:
			self._back.show()
			self._next.show()
		else:
			self._back.hide()
			self._next.hide()

	@misc_utils.log_exception(_moduleLogger)
	def _on_back_clicked(self, *args):
		self._player.back()

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
