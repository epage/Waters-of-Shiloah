import logging

import gobject
import pango
import cairo
import gtk

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

	MINIMUM_MOVEMENT = 20

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

		if self._isPortrait:
			delta = (
				newCoord[0] - self._clickPosition[0],
				- (newCoord[1] - self._clickPosition[1])
			)
		else:
			delta = (
				newCoord[1] - self._clickPosition[1],
				- (newCoord[0] - self._clickPosition[0])
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
			self.emit("action", state)
		finally:
			self._clickPosition = self._NO_POSITION

	@misc_utils.log_exception(_moduleLogger)
	def _on_motion_notify(self, widget, event):
		if self._clickPosition == self._NO_POSITION:
			return

		mousePosition = event.get_coords()
		newState = self.get_state(mousePosition)
		self.emit("navigating", newState)


gobject.type_register(NavigationBox)


class StreamPresenter(object):

	BUTTON_STATE_PLAY = "play"
	BUTTON_STATE_PAUSE = "pause"
	BUTTON_STATE_NEXT = "next"
	BUTTON_STATE_BACK = "back"
	BUTTON_STATE_UP = "up"
	BUTTON_STATE_CANCEL = "cancel"

	_STATE_TO_IMAGE = {
		BUTTON_STATE_PLAY: "play.png",
		BUTTON_STATE_PAUSE: "pause.png",
		BUTTON_STATE_NEXT: "next.png",
		BUTTON_STATE_BACK: "prev.png",
		BUTTON_STATE_UP: "home.png",
	}

	def __init__(self, player, store):
		self._store = store

		self._player = player
		self._player.connect("state-change", self._on_player_state_change)
		self._player.connect("navigate-change", self._on_player_nav_change)
		self._player.connect("title-change", self._on_player_title_change)

		self._image = gtk.DrawingArea()
		self._image.connect("expose_event", self._on_expose)
		self._imageNav = NavigationBox()
		self._imageNav.toplevel.add(self._image)
		self._imageNav.connect("navigating", self._on_navigating)
		self._imageNav.connect("action", self._on_nav_action)

		self._isPortrait = True

		self._canNavigate = True
		self._potentialButtonState = self.BUTTON_STATE_PLAY
		self._currentButtonState = self.BUTTON_STATE_PLAY

		imagePath = self._store.STORE_LOOKUP[self._player.background]
		self._backgroundImage = self._store.get_surface_from_store(imagePath)
		imagePath = self._STATE_TO_IMAGE[self._currentButtonState]
		self._buttonImage = self._store.get_surface_from_store(imagePath)

		if self._isPortrait:
			backWidth = self._backgroundImage.get_width()
			backHeight = self._backgroundImage.get_height()
		else:
			backHeight = self._backgroundImage.get_width()
			backWidth = self._backgroundImage.get_height()
		self._image.set_size_request(backWidth, backHeight)

	@property
	def toplevel(self):
		return self._imageNav.toplevel

	def set_orientation(self, orientation):
		self._imageNav.set_orientation(orientation)

		if orientation == gtk.ORIENTATION_VERTICAL:
			self._isPortrait = True
		elif orientation == gtk.ORIENTATION_HORIZONTAL:
			self._isPortrait = False
		else:
			raise NotImplementedError(orientation)

		cairoContext = self._image.window.cairo_create()
		if not self._isPortrait:
			cairoContext.transform(cairo.Matrix(0, 1, 1, 0, 0, 0))
		self._draw_presenter(cairoContext, self._currentButtonState)

	@misc_utils.log_exception(_moduleLogger)
	def _on_player_state_change(self, player, newState):
		# @bug We only want to folow changes in player when its active
		if newState == "play":
			newState = self.BUTTON_STATE_PLAY
		elif newState == "pause":
			newState = self.BUTTON_STATE_PAUSE
		elif newState == "stop":
			newState = self.BUTTON_STATE_PAUSE
		else:
			newState = self._currentButtonState

		if newState != self._currentButtonState:
			self._currentButtonState = newState
			if not self._imageNav.is_active():
				cairoContext = self._image.window.cairo_create()
				if not self._isPortrait:
					cairoContext.transform(cairo.Matrix(0, 1, 1, 0, 0, 0))
				self._draw_state(cairoContext, self._currentButtonState)

	@misc_utils.log_exception(_moduleLogger)
	def _on_player_nav_change(self, player, newState):
		# @bug We only want to folow changes in player when its active
		canNavigate = self._player.can_navigate
		newPotState = self._potentialButtonState
		if self._canNavigate != canNavigate:
			self._canNavigate = canNavigate
			if self._potentialButtonState in (self.BUTTON_STATE_NEXT, self.BUTTON_STATE_BACK):
				if self._currentButtonState == self.BUTTON_STATE_PLAY:
					newPotState = self.BUTTON_STATE_PAUSE
				else:
					newPotState = self.BUTTON_STATE_PLAY

		if newPotState != self._potentialButtonState:
			self._potentialButtonState = newPotState
			if not self._imageNav.is_active():
				cairoContext = self._image.window.cairo_create()
				if not self._isPortrait:
					cairoContext.transform(cairo.Matrix(0, 1, 1, 0, 0, 0))
				self._draw_state(cairoContext, self._potentialButtonState)

	@misc_utils.log_exception(_moduleLogger)
	def _on_player_title_change(self, player, newState):
		# @bug We only want to folow changes in player when its active
		if self._isPortrait:
			backWidth = self._backgroundImage.get_width()
			backHeight = self._backgroundImage.get_height()
		else:
			backHeight = self._backgroundImage.get_width()
			backWidth = self._backgroundImage.get_height()
		self._image.set_size_request(backWidth, backHeight)

		imagePath = self._store.STORE_LOOKUP[self._player.background]
		self._backgroundImage = self._store.get_surface_from_store(imagePath)
		if not self._imageNav.get_state():
			cairoContext = self._image.window.cairo_create()
			if not self._isPortrait:
				cairoContext.transform(cairo.Matrix(0, 1, 1, 0, 0, 0))
			self._draw_presenter(cairoContext, self._currentButtonState)
		else:
			cairoContext = self._image.window.cairo_create()
			if not self._isPortrait:
				cairoContext.transform(cairo.Matrix(0, 1, 1, 0, 0, 0))
			self._draw_presenter(cairoContext, self._potentialButtonState)

	@misc_utils.log_exception(_moduleLogger)
	def _on_navigating(self, widget, navState):
		buttonState = self._translate_state(navState)
		self._potentialButtonState = buttonState
		cairoContext = self._image.window.cairo_create()
		if not self._isPortrait:
			cairoContext.transform(cairo.Matrix(0, 1, 1, 0, 0, 0))
		self._draw_state(cairoContext, self._potentialButtonState)

	@misc_utils.log_exception(_moduleLogger)
	def _on_nav_action(self, widget, navState):
		# @bug We only want to folow changes in player when its active
		try:
			buttonState = self._translate_state(navState)
			if buttonState == self.BUTTON_STATE_PLAY:
				self._player.play()
			elif buttonState == self.BUTTON_STATE_PAUSE:
				self._player.pause()
			elif buttonState == self.BUTTON_STATE_NEXT:
				self._player.next()
			elif buttonState == self.BUTTON_STATE_BACK:
				self._player.back()
			elif buttonState == self.BUTTON_STATE_UP:
				raise NotImplementedError("Drag-down not implemented yet")
			elif buttonState == self.BUTTON_STATE_CANCEL:
				pass
		finally:
			if self._player.state == "play":
				buttonState = self.BUTTON_STATE_PLAY
			else:
				buttonState = self.BUTTON_STATE_PAUSE
			self._potentialButtonState = buttonState
			cairoContext = self._image.window.cairo_create()
			if not self._isPortrait:
				cairoContext.transform(cairo.Matrix(0, 1, 1, 0, 0, 0))
			self._draw_state(cairoContext, self._potentialButtonState)

	def _translate_state(self, navState):
		if navState == "clicking" or not self._canNavigate:
			if self._currentButtonState == self.BUTTON_STATE_PLAY:
				return self.BUTTON_STATE_PAUSE
			else:
				return self.BUTTON_STATE_PLAY
		elif navState == "down":
			return self.BUTTON_STATE_UP
		elif navState == "up":
			return self.BUTTON_STATE_CANCEL
		elif navState == "left":
			return self.BUTTON_STATE_NEXT
		elif navState == "right":
			return self.BUTTON_STATE_BACK

	@misc_utils.log_exception(_moduleLogger)
	def _on_expose(self, widget, event):
		self._potentialButtonState = self._player.state
		cairoContext = self._image.window.cairo_create()
		if not self._isPortrait:
			cairoContext.transform(cairo.Matrix(0, 1, 1, 0, 0, 0))
		self._draw_presenter(cairoContext, self._player.state)

	def _draw_presenter(self, cairoContext, state):
		assert state in (self._currentButtonState, self._potentialButtonState)

		# Blank things
		rect = self._image.get_allocation()
		cairoContext.rectangle(
			0,
			0,
			rect.width,
			rect.height,
		)
		cairoContext.set_source_rgb(0, 0, 0)
		cairoContext.fill()
		cairoContext.paint()

		# Draw Background
		cairoContext.set_source_surface(
			self._backgroundImage,
			0,
			0,
		)
		cairoContext.paint()

		# title
		if self._player.title:
			_moduleLogger.info("Displaying text")
			backWidth = self._backgroundImage.get_width()
			backHeight = self._backgroundImage.get_height()

			pangoContext = self._image.create_pango_context()
			textLayout = pango.Layout(pangoContext)
			textLayout.set_markup(self._player.title)

			textWidth, textHeight = textLayout.get_pixel_size()
			textX = backWidth / 2 - textWidth / 2
			textY = backHeight - textHeight - self._buttonImage.get_height()

			cairoContext.move_to(textX, textY)
			cairoContext.set_source_rgb(0, 0, 0)
			cairoContext.show_layout(textLayout)

		self._draw_state(cairoContext, state)

	def _draw_state(self, cairoContext, state):
		assert state in (self._currentButtonState, self._potentialButtonState)
		if state == self.BUTTON_STATE_CANCEL:
			state = self._currentButtonState

		backWidth = self._backgroundImage.get_width()
		backHeight = self._backgroundImage.get_height()

		imagePath = self._STATE_TO_IMAGE[state]
		self._buttonImage = self._store.get_surface_from_store(imagePath)
		cairoContext.set_source_surface(
			self._buttonImage,
			backWidth / 2 - self._buttonImage.get_width() / 2,
			backHeight - self._buttonImage.get_height() + 5,
		)
		cairoContext.paint()


class StreamMiniPresenter(object):

	def __init__(self, player, store):
		self._store = store
		self._player = player
		self._player.connect("state-change", self._on_player_state_change)

		self._button = gtk.Image()
		if self._player.state == "play":
			self._store.set_image_from_store(self._button, self._store.STORE_LOOKUP["play"])
		else:
			self._store.set_image_from_store(self._button, self._store.STORE_LOOKUP["pause"])

		self._eventBox = gtk.EventBox()
		self._eventBox.add(self._button)
		self._eventBox.connect("button_release_event", self._on_button_release)

	@property
	def toplevel(self):
		return self._eventBox

	@misc_utils.log_exception(_moduleLogger)
	def _on_player_state_change(self, player, newState):
		if self._player.state == "play":
			self._store.set_image_from_store(self._button, self._store.STORE_LOOKUP["play"])
		else:
			self._store.set_image_from_store(self._button, self._store.STORE_LOOKUP["pause"])

	@misc_utils.log_exception(_moduleLogger)
	def _on_button_release(self, widget, event):
		if self._player.state == "play":
			self._player.pause()
		else:
			self._player.play()
