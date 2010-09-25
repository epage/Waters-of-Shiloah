import sys
import logging

import gtk

import util.misc as misc_utils


_moduleLogger = logging.getLogger(__name__)


class GenericBanner(object):

	def __init__(self):
		self._indicator = gtk.Image()

		self._label = gtk.Label()

		self._layout = gtk.HBox()
		self._layout.pack_start(self._indicator, False, False)
		self._layout.pack_start(self._label, False, True)

	@property
	def toplevel(self):
		return self._layout

	def show(self, icon, message):
		assert not self._label.get_text(), self._label.get_text()
		if isinstance(icon, gtk.gdk.PixbufAnimation):
			self._indicator.set_from_animation(icon)
		elif isinstance(icon, gtk.gdk.Pixbuf):
			self._indicator.set_from_pixbuf(icon)
		else:
			self._indicator.set_from_stock(icon)
		self._label.set_text(message)
		self.toplevel.show()

	def hide(self):
		self._label.set_text("")
		self.toplevel.hide()


class StackingBanner(object):

	ICON_SIZE = 32

	def __init__(self):
		self._indicator = gtk.Image()

		self._message = gtk.Label()

		self._closeImage = gtk.Image()
		self._closeImage.set_from_stock("gtk-close", self.ICON_SIZE)

		self._layout = gtk.HBox()
		self._layout.pack_start(self._indicator, False, False)
		self._layout.pack_start(self._message, True, True)
		self._layout.pack_start(self._closeImage, False, False)

		self._events = gtk.EventBox()
		self._events.add(self._layout)
		self._events.connect("button_release_event", self._on_close)

		self._messages = []

	@property
	def toplevel(self):
		return self._events

	def push_message(self, message, icon=""):
		self._messages.append((message, icon))
		if 1 == len(self._messages):
			self._update_message()

	def push_exception(self):
		userMessage = str(sys.exc_info()[1])
		self.push_message(userMessage, "gtk-dialog-error")
		_moduleLogger.exception(userMessage)

	def pop_message(self):
		del self._messages[0]
		self._update_message()

	def _update_message(self):
		if 0 == len(self._messages):
			self.toplevel.hide()
		else:
			message, icon = self._messages[0]
			self._message.set_text(message)
			if icon:
				self._indicator.set_from_stock(icon)
				self._indicator.show()
			else:
				self._indicator.hide()
			self.toplevel.show()

	@misc_utils.log_exception(_moduleLogger)
	def _on_close(self, *args):
		self.pop_message()
