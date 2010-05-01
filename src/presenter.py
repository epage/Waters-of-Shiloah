import logging

import pango
import cairo
import gtk

import util.misc as misc_utils


_moduleLogger = logging.getLogger(__name__)


class StreamPresenter(object):

	MINIMUM_MOVEMENT = 20

	BUTTON_STATE_PLAY = "play"
	BUTTON_STATE_PAUSE = "pause"
	BUTTON_STATE_NEXT = "next"
	BUTTON_STATE_BACK = "back"
	BUTTON_STATE_UP = "up"
	BUTTON_STATE_CANCEL = "cancel"

	_NO_POSITION = -1, -1

	_STATE_TO_IMAGE = {
		BUTTON_STATE_PLAY: "play.png",
		BUTTON_STATE_PAUSE: "pause.png",
		BUTTON_STATE_NEXT: "next.png",
		BUTTON_STATE_BACK: "prev.png",
	}

	def __init__(self, player, store):
		self._store = store

		self._player = player
		self._player.connect("state-change", self._on_player_state_change)
		self._player.connect("navigate-change", self._on_player_nav_change)
		self._player.connect("title-change", self._on_player_title_change)

		self._image = gtk.DrawingArea()
		self._image.connect("expose_event", self._on_expose)
		self._imageEvents = gtk.EventBox()
		self._imageEvents.connect("motion_notify_event", self._on_motion_notify)
		#self._imageEvents.connect("leave_notify_event", self._on_leave_notify)
		#self._imageEvents.connect("proximity_in_event", self._on_motion_notify)
		#self._imageEvents.connect("proximity_out_event", self._on_leave_notify)
		self._imageEvents.connect("button_press_event", self._on_button_press)
		self._imageEvents.connect("button_release_event", self._on_button_release)
		self._imageEvents.add(self._image)

		self._isPortrait = True

		self._canNavigate = True
		self._clickPosition = self._NO_POSITION
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
		return self._imageEvents

	def set_orientation(self, orientation):
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
			if self._clickPosition == self._NO_POSITION:
				cairoContext = self._image.window.cairo_create()
				if not self._isPortrait:
					cairoContext.transform(cairo.Matrix(0, 1, 1, 0, 0, 0))
				self._draw_state(cairoContext, self._currentButtonState)

	@misc_utils.log_exception(_moduleLogger)
	def _on_player_nav_change(self, player, newState):
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
			if self._clickPosition == self._NO_POSITION:
				cairoContext = self._image.window.cairo_create()
				if not self._isPortrait:
					cairoContext.transform(cairo.Matrix(0, 1, 1, 0, 0, 0))
				self._draw_state(cairoContext, self._potentialButtonState)

	@misc_utils.log_exception(_moduleLogger)
	def _on_player_title_change(self, player, newState):
		if self._isPortrait:
			backWidth = self._backgroundImage.get_width()
			backHeight = self._backgroundImage.get_height()
		else:
			backHeight = self._backgroundImage.get_width()
			backWidth = self._backgroundImage.get_height()
		self._image.set_size_request(backWidth, backHeight)

		imagePath = self._store.STORE_LOOKUP[self._player.background]
		self._backgroundImage = self._store.get_surface_from_store(imagePath)
		if self._clickPosition == self._NO_POSITION:
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
	def _on_button_press(self, widget, event):
		self._clickPosition = event.get_coords()
		if self._currentButtonState == self.BUTTON_STATE_PLAY:
			newState = self.BUTTON_STATE_PAUSE
		else:
			newState = self.BUTTON_STATE_PLAY
		self._potentialButtonState = newState
		cairoContext = self._image.window.cairo_create()
		if not self._isPortrait:
			cairoContext.transform(cairo.Matrix(0, 1, 1, 0, 0, 0))
		self._draw_state(cairoContext, self._potentialButtonState)

	@misc_utils.log_exception(_moduleLogger)
	def _on_button_release(self, widget, event):
		try:
			mousePosition = event.get_coords()
			newState = self._calculate_state(mousePosition)
			if newState == self.BUTTON_STATE_PLAY:
				self._player.play()
			elif newState == self.BUTTON_STATE_PAUSE:
				self._player.pause()
			elif newState == self.BUTTON_STATE_NEXT:
				self._player.next()
			elif newState == self.BUTTON_STATE_BACK:
				self._player.back()
			elif newState == self.BUTTON_STATE_UP:
				raise NotImplementedError("Drag-down not implemented yet")
			elif newState == self.BUTTON_STATE_CANCEL:
				pass
		finally:
			if self._player.state == "play":
				newState = self.BUTTON_STATE_PLAY
			else:
				newState = self.BUTTON_STATE_PAUSE
			self._potentialButtonState = newState
			cairoContext = self._image.window.cairo_create()
			if not self._isPortrait:
				cairoContext.transform(cairo.Matrix(0, 1, 1, 0, 0, 0))
			self._draw_state(cairoContext, self._potentialButtonState)
			self._clickPosition = self._NO_POSITION

	@misc_utils.log_exception(_moduleLogger)
	def _on_motion_notify(self, widget, event):
		if self._clickPosition == self._NO_POSITION:
			return

		mousePosition = event.get_coords()
		newState = self._calculate_state(mousePosition)
		if newState != self._potentialButtonState:
			self._potentialButtonState = newState
			cairoContext = self._image.window.cairo_create()
			if not self._isPortrait:
				cairoContext.transform(cairo.Matrix(0, 1, 1, 0, 0, 0))
			self._draw_state(cairoContext, self._potentialButtonState)

	def _calculate_state(self, newCoord):
		assert self._clickPosition != self._NO_POSITION

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
		if max(*absDelta) < self.MINIMUM_MOVEMENT or not self._canNavigate:
			if self._currentButtonState == self.BUTTON_STATE_PLAY:
				return self.BUTTON_STATE_PAUSE
			else:
				return self.BUTTON_STATE_PLAY

		if absDelta[0] < absDelta[1]:
			if 0 < delta[1]:
				return self.BUTTON_STATE_CANCEL
			else:
				return self.BUTTON_STATE_UP
		else:
			if 0 < delta[0]:
				return self.BUTTON_STATE_BACK
			else:
				return self.BUTTON_STATE_NEXT

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
