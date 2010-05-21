import logging

import gobject
import pango
import gtk

import util.go_utils as go_utils
import util.misc as misc_utils


_moduleLogger = logging.getLogger(__name__)


class NavigationBox(gobject.GObject):

	__gsignals__ = {
		'action' : (
			gobject.SIGNAL_RUN_LAST,
			gobject.TYPE_NONE,
			(gobject.TYPE_STRING, ),
		),
		'navigating' : (
			gobject.SIGNAL_RUN_LAST,
			gobject.TYPE_NONE,
			(gobject.TYPE_STRING, ),
		),
	}

	MINIMUM_MOVEMENT = 32

	_NO_POSITION = -1, -1

	def __init__(self):
		gobject.GObject.__init__(self)
		self._eventBox = gtk.EventBox()
		self._eventBox.connect("button_press_event", self._on_button_press)
		self._eventBox.connect("button_release_event", self._on_button_release)
		self._eventBox.connect("motion_notify_event", self._on_motion_notify)

		self._isPortrait = True
		self._clickPosition = self._NO_POSITION

	@property
	def toplevel(self):
		return self._eventBox

	def set_orientation(self, orientation):
		if orientation == gtk.ORIENTATION_VERTICAL:
			self._isPortrait = True
		elif orientation == gtk.ORIENTATION_HORIZONTAL:
			self._isPortrait = False
		else:
			raise NotImplementedError(orientation)

	def is_active(self):
		return self._clickPosition != self._NO_POSITION

	def get_state(self, newCoord):
		if self._clickPosition == self._NO_POSITION:
			return ""

		delta = (
			newCoord[0] - self._clickPosition[0],
			- (newCoord[1] - self._clickPosition[1])
		)
		absDelta = (abs(delta[0]), abs(delta[1]))
		if max(*absDelta) < self.MINIMUM_MOVEMENT:
			return "clicking"

		if absDelta[0] < absDelta[1]:
			if 0 < delta[1]:
				return "up"
			else:
				return "down"
		else:
			if 0 < delta[0]:
				return "right"
			else:
				return "left"

	@misc_utils.log_exception(_moduleLogger)
	def _on_button_press(self, widget, event):
		if self._clickPosition != self._NO_POSITION:
			_moduleLogger.debug("Ignoring double click")
		self._clickPosition = event.get_coords()

		self.emit("navigating", "clicking")

	@misc_utils.log_exception(_moduleLogger)
	def _on_button_release(self, widget, event):
		assert self._clickPosition != self._NO_POSITION
		try:
			mousePosition = event.get_coords()
			state = self.get_state(mousePosition)
			assert state
		finally:
			self._clickPosition = self._NO_POSITION
		self.emit("action", state)

	@misc_utils.log_exception(_moduleLogger)
	def _on_motion_notify(self, widget, event):
		if self._clickPosition == self._NO_POSITION:
			return

		mousePosition = event.get_coords()
		newState = self.get_state(mousePosition)
		self.emit("navigating", newState)


gobject.type_register(NavigationBox)


class StreamPresenter(object):

	def __init__(self, store):
		self._store = store

		self._image = gtk.DrawingArea()
		self._image.connect("expose_event", self._on_expose)

		self._isPortrait = True

		self._backgroundImage = None
		self._title = ""
		self._subtitle = ""
		self._buttonImage = None
		self._imageName = ""
		self._dims = 0, 0

	@property
	def toplevel(self):
		return self._image

	def set_orientation(self, orientation):
		if orientation == gtk.ORIENTATION_VERTICAL:
			self._isPortrait = True
		elif orientation == gtk.ORIENTATION_HORIZONTAL:
			self._isPortrait = False
		else:
			raise NotImplementedError(orientation)

		self._image.queue_draw()

	def set_state(self, stateImage):
		if stateImage == self._imageName:
			return
		self._imageName = stateImage
		self._buttonImage = self._store.get_surface_from_store(stateImage)

		self._image.queue_draw()

	def set_context(self, backgroundImage, title, subtitle):
		self._backgroundImage = self._store.get_surface_from_store(backgroundImage)
		self._title = title
		self._subtitle = subtitle

		backWidth = self._backgroundImage.get_width()
		backHeight = self._backgroundImage.get_height()
		self._image.set_size_request(backWidth, backHeight)

		self._image.queue_draw()

	@misc_utils.log_exception(_moduleLogger)
	def _on_expose(self, widget, event):
		cairoContext = self._image.window.cairo_create()
		self._draw_presenter(cairoContext)

	def _draw_presenter(self, cairoContext):
		rect = self._image.get_allocation()
		self._dims = rect.width, rect.height

		# Blank things
		cairoContext.rectangle(
			0,
			0,
			rect.width,
			rect.height,
		)
		cairoContext.set_source_rgb(0, 0, 0)
		cairoContext.fill()

		# Draw Background
		if self._backgroundImage is not None:
			cairoContext.set_source_surface(
				self._backgroundImage,
				0,
				0,
			)
			cairoContext.paint()

		pangoContext = self._image.create_pango_context()

		titleLayout = pango.Layout(pangoContext)
		titleLayout.set_markup("<i>%s</i>" % self._subtitle)
		textWidth, textHeight = titleLayout.get_pixel_size()
		subtitleTextX = self._dims[0] / 2 - textWidth / 2
		subtitleTextY = self._dims[1] - textHeight - self._buttonImage.get_height() + 10

		subtitleLayout = pango.Layout(pangoContext)
		subtitleLayout.set_markup("<b>%s</b>" % self._title)
		textWidth, textHeight = subtitleLayout.get_pixel_size()
		textX = self._dims[0] / 2 - textWidth / 2
		textY = subtitleTextY - textHeight

		xPadding = min((self._dims[0] - textWidth) / 2 - 5, 5)
		yPadding = 5
		startContent = xPadding, textY - yPadding
		endContent = self._dims[0] - xPadding,  self._dims[1] - yPadding

		# Control background
		cairoContext.rectangle(
			startContent[0],
			startContent[1],
			endContent[0] - startContent[0],
			endContent[1] - startContent[1],
		)
		cairoContext.set_source_rgba(0.9, 0.9, 0.9, 0.75)
		cairoContext.fill()

		# title
		if self._title or self._subtitle:
			cairoContext.move_to(subtitleTextX, subtitleTextY)
			cairoContext.set_source_rgb(0, 0, 0)
			cairoContext.show_layout(titleLayout)

			cairoContext.move_to(textX, textY)
			cairoContext.set_source_rgb(0, 0, 0)
			cairoContext.show_layout(subtitleLayout)

		self._draw_state(cairoContext)

	def _draw_state(self, cairoContext):
		if self._backgroundImage is None or self._buttonImage is None:
			return
		cairoContext.set_source_surface(
			self._buttonImage,
			self._dims[0] / 2 - self._buttonImage.get_width() / 2,
			self._dims[1] - self._buttonImage.get_height() + 5,
		)
		cairoContext.paint()


class StreamMiniPresenter(object):

	def __init__(self, store):
		self._store = store

		self._button = gtk.Image()

	@property
	def toplevel(self):
		return self._button

	def set_orientation(self, orientation):
		pass

	def set_state(self, stateImage):
		self._store.set_image_from_store(self._button, stateImage)

	def set_context(self, backgroundImage, title, subtitle):
		pass


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

		self._controlBox = NavigationBox()
		self._controlBox.toplevel.add(self._controlButton)
		self._controlBox.connect("action", self._on_nav_action)
		self._controlBox.connect("navigating", self._on_navigating)

		self._titleButton = gtk.Label()

		self._displayBox = NavigationBox()
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
