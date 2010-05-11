import logging

import gobject
import gtk

import gtk_toolbox
import hildonize
import util.misc as misc_utils

import presenter


_moduleLogger = logging.getLogger(__name__)


class NavControl(gobject.GObject):


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

		self._player = player
		self._player.connect("state-change", self._on_player_state_change)
		self._player.connect("title-change", self._on_player_title_change)

		self._controlButton = store.get_image_from_store(store.STORE_LOOKUP["small_play"])

		self._controlBox = presenter.NavigationBox()
		self._controlBox.toplevel.add(self._controlButton)
		self._controlBox.connect("action", self._on_nav_action)
		self._controlBox.connect("navigating", self._on_navigating)

		self._titleButton = gtk.Label("")

		self._displayBox = presenter.NavigationBox()
		self._displayBox.toplevel.add(self._titleButton)
		self._displayBox.connect("action", self._on_nav_action)
		self._displayBox.connect("navigating", self._on_navigating)

		self._layout = gtk.HBox()
		self._layout.pack_start(self._controlBox.toplevel, False, False)
		self._layout.pack_start(self._displayBox.toplevel, False, True)

	def refresh(self):
		if not self._player.title:
			self.toplevel.hide()

	@property
	def toplevel(self):
		return self._layout

	def set_orientation(self, orientation):
		pass

	@misc_utils.log_exception(_moduleLogger)
	def _on_player_state_change(self, player, newState):
		if self._controlBox.is_active() or self._displayBox.is_active():
			return

		if newState == "play":
			stateImage = self._store.STORE_LOOKUP["small_play"]
			self._store.set_image_from_store(self._controlButton, stateImage)
			self.toplevel.show()
		elif newState == "pause":
			stateImage = self._store.STORE_LOOKUP["small_pause"]
			self._store.set_image_from_store(self._controlButton, stateImage)
			self.toplevel.show()
		elif newState == "stop":
			self._titleButton.set_label("")
			self.toplevel.hide()
		else:
			_moduleLogger.info("Unhandled player state %s" % newState)
			stateImage = self._store.STORE_LOOKUP["small_pause"]
			self._store.set_image_from_store(self._controlButton, stateImage)

	@misc_utils.log_exception(_moduleLogger)
	def _on_player_title_change(self, player, newState):
		self._titleButton.set_label(self._player.title)

	@misc_utils.log_exception(_moduleLogger)
	def _on_navigating(self, widget, navState):
		if navState == "down":
			imageName = "small_home"
		elif navState == "up":
			imageName = "small_play"
		elif navState == "clicking" or not self._player.can_navigate:
			if widget is self._controlBox:
				if self._player.state == "play":
					imageName = "small_pause"
				else:
					imageName = "small_play"
			elif widget is self._displayBox:
				if self._player.state == "play":
					imageName = "small_play"
				else:
					imageName = "small_pause"
			else:
				raise NotImplementedError()
		elif navState == "left":
			imageName = "small_next"
		elif navState == "right":
			imageName = "small_prev"

		imagePath = self._store.STORE_LOOKUP[imageName]
		self._store.set_image_from_store(self._controlButton, imagePath)

	@misc_utils.log_exception(_moduleLogger)
	def _on_nav_action(self, widget, navState):
		if self._player.state == "play":
			imageName = "small_play"
		else:
			imageName = "small_pause"
		imagePath = self._store.STORE_LOOKUP[imageName]
		self._store.set_image_from_store(self._controlButton, imagePath)

		if navState == "clicking":
			if widget is self._controlBox:
				if self._player.state == "play":
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


class PlayControl(object):

	def __init__(self, player, store):
		self._isPortrait = True

		self._store = store

		self._player = player
		self._player.connect("state-change", self._on_player_state_change)
		self._player.connect("title-change", self._on_player_nav_change)

		img = store.get_image_from_store(store.STORE_LOOKUP["small_prev"])
		self._back = gtk.Button()
		self._back.set_image(img)
		self._back.connect("clicked", self._on_back_clicked)

		img = store.get_image_from_store(store.STORE_LOOKUP["small_stop"])
		self._stop = gtk.Button()
		self._stop.set_image(img)
		self._stop.connect("clicked", self._on_stop_clicked)

		img = store.get_image_from_store(store.STORE_LOOKUP["small_pause"])
		self._pause = gtk.Button()
		self._pause.set_image(img)
		self._pause.connect("clicked", self._on_pause_clicked)

		img = store.get_image_from_store(store.STORE_LOOKUP["small_play"])
		self._play = gtk.Button()
		self._play.set_image(img)
		self._play.connect("clicked", self._on_play_clicked)

		img = store.get_image_from_store(store.STORE_LOOKUP["small_next"])
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
