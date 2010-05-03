import ConfigParser
import logging

import gobject
import gtk

import constants
import hildonize
import gtk_toolbox
import util.misc as misc_utils

import banners
import playcontrol


_moduleLogger = logging.getLogger(__name__)


class BasicWindow(gobject.GObject):

	__gsignals__ = {
		'quit' : (
			gobject.SIGNAL_RUN_LAST,
			gobject.TYPE_NONE,
			(),
		),
		'fullscreen' : (
			gobject.SIGNAL_RUN_LAST,
			gobject.TYPE_NONE,
			(gobject.TYPE_PYOBJECT, ),
		),
	}

	def __init__(self, player, store):
		gobject.GObject.__init__(self)

		self._player = player
		self._store = store

		self._clipboard = gtk.clipboard_get()
		self._windowInFullscreen = False

		self._errorBanner = banners.StackingBanner()

		self._layout = gtk.VBox()
		self._layout.pack_start(self._errorBanner.toplevel, False, True)

		self._window = gtk.Window()
		self._window.add(self._layout)
		self._window = hildonize.hildonize_window(self, self._window)

		hildonize.set_application_title(self._window, "%s" % constants.__pretty_app_name__)
		self._window.set_icon(self._store.get_pixbuf_from_store(self._store.STORE_LOOKUP["icon"]))
		self._window.connect("key-press-event", self._on_key_press)
		self._window.connect("window-state-event", self._on_window_state_change)

	@property
	def window(self):
		return self._window

	def save_settings(self, config, sectionName):
		config.add_section(sectionName)
		config.set(sectionName, "fullscreen", str(self._windowInFullscreen))

	def load_settings(self, config, sectionName):
		try:
			self._windowInFullscreen = config.getboolean(sectionName, "fullscreen")
		except ConfigParser.NoSectionError, e:
			_moduleLogger.info(
				"Settings file %s is missing section %s" % (
					constants._user_settings_,
					e.section,
				)
			)

		if self._windowInFullscreen:
			self._window.fullscreen()
		else:
			self._window.unfullscreen()

	@misc_utils.log_exception(_moduleLogger)
	def _on_window_state_change(self, widget, event, *args):
		if event.new_window_state & gtk.gdk.WINDOW_STATE_FULLSCREEN:
			self._windowInFullscreen = True
		else:
			self._windowInFullscreen = False
		self.emit("fullscreen", self._windowInFullscreen)

	@misc_utils.log_exception(_moduleLogger)
	def _on_key_press(self, widget, event, *args):
		RETURN_TYPES = (gtk.keysyms.Return, gtk.keysyms.ISO_Enter, gtk.keysyms.KP_Enter)
		isCtrl = bool(event.get_state() & gtk.gdk.CONTROL_MASK)
		if (
			event.keyval == gtk.keysyms.F6 or
			event.keyval in RETURN_TYPES and isCtrl
		):
			# The "Full screen" hardware key has been pressed
			if self._windowInFullscreen:
				self._window.unfullscreen ()
			else:
				self._window.fullscreen ()
			return True
		elif (
			event.keyval in (gtk.keysyms.w, ) and
			event.get_state() & gtk.gdk.CONTROL_MASK
		):
			self._window.destroy()
		elif (
			event.keyval in (gtk.keysyms.q, ) and
			event.get_state() & gtk.gdk.CONTROL_MASK
		):
			self.emit("quit")
		elif event.keyval == gtk.keysyms.l and event.get_state() & gtk.gdk.CONTROL_MASK:
			with open(constants._user_logpath_, "r") as f:
				logLines = f.xreadlines()
				log = "".join(logLines)
				self._clipboard.set_text(str(log))
			return True


class SourceSelector(BasicWindow):

	def __init__(self, player, store):
		BasicWindow.__init__(self, player, store)

		self._radioButton = self._create_button("radio", "Radio")
		self._radioButton.connect("clicked", self._on_radio_selected)
		self._radioWrapper = gtk.VBox()
		self._radioWrapper.pack_start(self._radioButton, False, True)

		self._conferenceButton = self._create_button("conferences", "Conferences")
		#self._conferenceButton.connect("clicked", self._on_conference_selected)
		self._conferenceWrapper = gtk.VBox()
		self._conferenceWrapper.pack_start(self._conferenceButton, False, True)

		self._magazineButton = self._create_button("magazines", "Magazines")
		#self._magazineButton.connect("clicked", self._on_magazine_selected)
		self._magazineWrapper = gtk.VBox()
		self._magazineWrapper.pack_start(self._magazineButton, False, True)

		self._scriptureButton = self._create_button("scriptures", "Scriptures")
		#self._scriptureButton.connect("clicked", self._on_scripture_selected)
		self._scriptureWrapper = gtk.VBox()
		self._scriptureWrapper.pack_start(self._scriptureButton, False, True)

		self._buttonLayout = gtk.VBox(True, 5)
		self._buttonLayout.set_property("border-width", 5)
		self._buttonLayout.pack_start(self._radioWrapper, True, True)
		self._buttonLayout.pack_start(self._conferenceWrapper, True, True)
		self._buttonLayout.pack_start(self._magazineWrapper, True, True)
		self._buttonLayout.pack_start(self._scriptureWrapper, True, True)

		self._playcontrol = playcontrol.PlayControl(player, store)

		self._layout.pack_start(self._buttonLayout, True, True)
		self._layout.pack_start(self._playcontrol.toplevel, False, True)

		self._window.show_all()
		self._errorBanner.toplevel.hide()
		self._playcontrol.toplevel.hide()

	def _create_button(self, icon, message):
		image = self._store.get_image_from_store(self._store.STORE_LOOKUP[icon])

		label = gtk.Label()
		label.set_text(message)

		buttonLayout = gtk.HBox(False, 5)
		buttonLayout.pack_start(image, False, False)
		buttonLayout.pack_start(label, False, True)
		button = gtk.Button()
		button.add(buttonLayout)

		return button

	@misc_utils.log_exception(_moduleLogger)
	def _on_radio_selected(self, *args):
		radioView = RadioView(self._player, self._store)
		radioView.window.set_modal(True)
		radioView.window.set_transient_for(self._window)
		radioView.window.set_default_size(*self._window.get_size())


class RadioView(BasicWindow):

	def __init__(self, player, store):
		BasicWindow.__init__(self, player, store)

		self._loadingBanner = banners.GenericBanner()

		headerPath = self._store.STORE_LOOKUP["radio_header"]
		self._header = self._store.get_image_from_store(headerPath)

		self._radioLayout = gtk.VBox(True, 5)
		self._radioLayout.set_property("border-width", 5)
		self._radioLayout.pack_start(self._header, False, False)

		self._layout.pack_start(self._loadingBanner.toplevel, False, False)
		self._layout.pack_start(self._radioLayout, True, True)

		self._window.show_all()
		self._errorBanner.toplevel.hide()
		self._loadingBanner.toplevel.hide()

	def _show_loading(self):
		animationPath = self._store.STORE_LOOKUP["loading"]
		animation = self._store.get_pixbuf_animation_from_store(animationPath)
		self._loadingBanner.show(animation, "Loading...")

	def _hide_loading(self):
		self._loadingBanner.hide()
