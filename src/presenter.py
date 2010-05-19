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
		titleLayout.set_markup(self._subtitle)
		textWidth, textHeight = titleLayout.get_pixel_size()
		subtitleTextX = self._dims[0] / 2 - textWidth / 2
		subtitleTextY = self._dims[1] - textHeight - self._buttonImage.get_height() + 10

		subtitleLayout = pango.Layout(pangoContext)
		subtitleLayout.set_markup(self._title)
		textWidth, textHeight = subtitleLayout.get_pixel_size()
		textX = self._dims[0] / 2 - textWidth / 2
		textY = subtitleTextY - textHeight

		startContent = 30, textY - 5
		endContent = self._dims[0] - 30,  self._dims[1] - 5

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
