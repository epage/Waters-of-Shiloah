import ConfigParser
import datetime
import logging

import gobject
import gtk

import constants
import hildonize
import util.misc as misc_utils

import banners
import playcontrol
import presenter


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

	def __init__(self, player, store, index):
		gobject.GObject.__init__(self)
		self._isDestroyed = False

		self._player = player
		self._store = store
		self._index = index

		self._clipboard = gtk.clipboard_get()
		self._windowInFullscreen = False

		self._errorBanner = banners.StackingBanner()

		self._layout = gtk.VBox()
		self._layout.pack_start(self._errorBanner.toplevel, False, True)

		self._window = gtk.Window()
		self._window.add(self._layout)
		self._window = hildonize.hildonize_window(self, self._window)

		self._window.set_icon(self._store.get_pixbuf_from_store(self._store.STORE_LOOKUP["icon"]))
		self._window.connect("key-press-event", self._on_key_press)
		self._window.connect("window-state-event", self._on_window_state_change)
		self._window.connect("destroy", self._on_destroy)

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
	def _on_destroy(self, *args):
		self._isDestroyed = True

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

	def __init__(self, player, store, index):
		BasicWindow.__init__(self, player, store, index)

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

		self._window.set_title(constants.__pretty_app_name__)
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
		radioView = RadioView(self._player, self._store, self._index)
		radioView.window.set_modal(True)
		radioView.window.set_transient_for(self._window)
		radioView.window.set_default_size(*self._window.get_size())


class RadioView(BasicWindow):

	def __init__(self, player, store, index):
		BasicWindow.__init__(self, player, store, index)

		self._loadingBanner = banners.GenericBanner()

		headerPath = self._store.STORE_LOOKUP["radio_header"]
		self._header = self._store.get_image_from_store(headerPath)

		self._programmingModel = gtk.ListStore(
			gobject.TYPE_STRING,
			gobject.TYPE_STRING,
		)

		textrenderer = gtk.CellRendererText()
		timeColumn = gtk.TreeViewColumn("Time")
		timeColumn.pack_start(textrenderer, expand=True)
		timeColumn.add_attribute(textrenderer, "text", 0)

		textrenderer = gtk.CellRendererText()
		titleColumn = gtk.TreeViewColumn("Program")
		titleColumn.pack_start(textrenderer, expand=True)
		titleColumn.add_attribute(textrenderer, "text", 1)

		self._treeView = gtk.TreeView()
		self._treeView.set_headers_visible(False)
		self._treeView.set_model(self._programmingModel)
		self._treeView.append_column(timeColumn)
		self._treeView.append_column(titleColumn)

		self._treeScroller = gtk.ScrolledWindow()
		self._treeScroller.add(self._treeView)
		self._treeScroller.set_policy(gtk.POLICY_NEVER, gtk.POLICY_AUTOMATIC)

		self._presenter = presenter.StreamMiniPresenter(self._player, self._store)

		self._radioLayout = gtk.VBox(False)
		self._radioLayout.pack_start(self._header, False, False)
		self._radioLayout.pack_start(self._treeScroller, True, True)
		self._radioLayout.pack_start(self._presenter.toplevel, False, True)

		self._programNavigation = presenter.NavigationBox()
		self._programNavigation.toplevel.add(self._radioLayout)
		self._programNavigation.connect("action", self._on_nav_action)

		self._layout.pack_start(self._loadingBanner.toplevel, False, False)
		self._layout.pack_start(self._programNavigation.toplevel, True, True)

		self._window.set_title("Radio")
		self._window.show_all()
		self._errorBanner.toplevel.hide()
		self._loadingBanner.toplevel.hide()

		self._dateShown = datetime.datetime.now()
		self._refresh()

	def _show_loading(self):
		animationPath = self._store.STORE_LOOKUP["loading"]
		animation = self._store.get_pixbuf_animation_from_store(animationPath)
		self._loadingBanner.show(animation, "Loading...")

	def _hide_loading(self):
		self._loadingBanner.hide()

	def _refresh(self):
		self._programmingModel.clear()
		self._show_loading()
		self._index.download_radio(self._on_channels, self._on_load_error)

	@misc_utils.log_exception(_moduleLogger)
	def _on_nav_action(self, widget, navState):
		_moduleLogger.info(navState)
		if navState == "clicking":
			pass
		elif navState == "down":
			self.window.destroy()
		elif navState == "up":
			pass
		elif navState == "left":
			self._dateShown += datetime.timedelta(days=1)
			self._refresh()
		elif navState == "right":
			self._dateShown -= datetime.timedelta(days=1)
			self._refresh()

	@misc_utils.log_exception(_moduleLogger)
	def _on_channels(self, channels):
		if self._isDestroyed:
			_moduleLogger.info("Download complete but window destroyed")
			return

		channels = list(channels)
		if 1 < len(channels):
			_moduleLogger.warning("More channels now available!")
		channel = channels[0]
		self._index.download_radio(self._on_channel, self._on_load_error, channel["id"])

	@misc_utils.log_exception(_moduleLogger)
	def _on_channel(self, programs):
		if self._isDestroyed:
			_moduleLogger.info("Download complete but window destroyed")
			return

		self._hide_loading()
		for program in programs:
			row = program["time"], program["title"]
			self._programmingModel.append(row)

		path = (self._get_current_row(), )
		self._treeView.scroll_to_cell(path)
		self._treeView.get_selection().select_path(path)

	def _get_current_row(self):
		nowTime = self._dateShown.strftime("%H:%M:%S")
		for i, row in enumerate(self._programmingModel):
			if nowTime < row[0]:
				return i - 1
		else:
			return i

	@misc_utils.log_exception(_moduleLogger)
	def _on_load_error(self, exception):
		self._hide_loading()
		self._errorBanner.push_message(exception)
