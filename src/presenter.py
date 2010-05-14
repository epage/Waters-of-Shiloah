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

		cairoContext = self._image.window.cairo_create()
		if not self._isPortrait:
			cairoContext.transform(cairo.Matrix(0, 1, 1, 0, 0, 0))
		self._draw_presenter(cairoContext)

	def set_state(self, stateImage):
		if stateImage == self._imageName:
			return
		self._imageName = stateImage
		self._buttonImage = self._store.get_surface_from_store(stateImage)

		cairoContext = self._image.window.cairo_create()
		if not self._isPortrait:
			cairoContext.transform(cairo.Matrix(0, 1, 1, 0, 0, 0))
		self._draw_presenter(cairoContext)

	def set_context(self, backgroundImage, title, subtitle):
		self._backgroundImage = self._store.get_surface_from_store(backgroundImage)

		if self._isPortrait:
			backWidth = self._backgroundImage.get_width()
			backHeight = self._backgroundImage.get_height()
		else:
			backHeight = self._backgroundImage.get_width()
			backWidth = self._backgroundImage.get_height()
		self._image.set_size_request(backWidth, backHeight)

		cairoContext = self._image.window.cairo_create()
		if not self._isPortrait:
			cairoContext.transform(cairo.Matrix(0, 1, 1, 0, 0, 0))
		self._draw_presenter(cairoContext)

	@misc_utils.log_exception(_moduleLogger)
	def _on_expose(self, widget, event):
		cairoContext = self._image.window.cairo_create()
		if not self._isPortrait:
			cairoContext.transform(cairo.Matrix(0, 1, 1, 0, 0, 0))
		self._draw_presenter(cairoContext)

	def _draw_presenter(self, cairoContext):
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
		if self._backgroundImage is not None:
			cairoContext.set_source_surface(
				self._backgroundImage,
				0,
				0,
			)
			cairoContext.paint()

		# title
		if self._title or self._subtitle:
			backWidth = self._backgroundImage.get_width()
			backHeight = self._backgroundImage.get_height()

			pangoContext = self._image.create_pango_context()
			textLayout = pango.Layout(pangoContext)

			textLayout.set_markup(self._subtitle)
			textWidth, textHeight = textLayout.get_pixel_size()
			subtitleTextX = backWidth / 2 - textWidth / 2
			subtitleTextY = backHeight - textHeight - self._buttonImage.get_height()
			cairoContext.move_to(subtitleTextX, subtitleTextY)
			cairoContext.set_source_rgb(0, 0, 0)
			cairoContext.show_layout(textLayout)

			textLayout.set_markup(self._title)
			textWidth, textHeight = textLayout.get_pixel_size()
			textX = backWidth / 2 - textWidth / 2
			textY = subtitleTextY - textHeight
			cairoContext.move_to(textX, textY)
			cairoContext.set_source_rgb(0, 0, 0)
			cairoContext.show_layout(textLayout)

		self._draw_state(cairoContext)

	def _draw_state(self, cairoContext):
		if self._backgroundImage is None or self._buttonImage is None:
			return
		backWidth = self._backgroundImage.get_width()
		backHeight = self._backgroundImage.get_height()

		cairoContext.set_source_surface(
			self._buttonImage,
			backWidth / 2 - self._buttonImage.get_width() / 2,
			backHeight - self._buttonImage.get_height() + 5,
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
