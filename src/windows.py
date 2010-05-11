# @todo Add icons to buttons/rows to indicate that the currently playing track is coming from that

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
		'rotate' : (
			gobject.SIGNAL_RUN_LAST,
			gobject.TYPE_NONE,
			(gobject.TYPE_BOOLEAN, ),
		),
		'fullscreen' : (
			gobject.SIGNAL_RUN_LAST,
			gobject.TYPE_NONE,
			(gobject.TYPE_BOOLEAN, ),
		),
	}

	def __init__(self, player, store):
		gobject.GObject.__init__(self)
		self._isDestroyed = False

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

		self._window.set_icon(self._store.get_pixbuf_from_store(self._store.STORE_LOOKUP["icon"]))
		self._window.connect("key-press-event", self._on_key_press)
		self._window.connect("window-state-event", self._on_window_state_change)
		self._window.connect("destroy", self._on_destroy)

	@property
	def window(self):
		return self._window

	def show(self):
		self._window.show_all()

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

	@misc_utils.log_exception(_moduleLogger)
	def _on_home(self, *args):
		self.emit("home")
		self._window.destroy()

	@misc_utils.log_exception(_moduleLogger)
	def _on_jump(self, source, node):
		_moduleLogger.error("Jump is not implemented")
		self.emit("jump-to", node)
		self._window.destroy()

	@misc_utils.log_exception(_moduleLogger)
	def _on_quit(self, *args):
		self.emit("quit")
		self._window.destroy()


class SourceSelector(BasicWindow):

	def __init__(self, player, store, index):
		BasicWindow.__init__(self, player, store)
		self._languages = []
		self._index = index

		self._loadingBanner = banners.GenericBanner()

		self._radioButton = self._create_button("radio", "Radio")
		self._radioButton.connect("clicked", self._on_source_selected, RadioWindow, "radio")
		self._radioWrapper = gtk.VBox()
		self._radioWrapper.pack_start(self._radioButton, False, True)

		self._conferenceButton = self._create_button("conferences", "Conferences")
		self._conferenceButton.connect("clicked", self._on_source_selected, ConferencesWindow, "conferences")
		self._conferenceWrapper = gtk.VBox()
		self._conferenceWrapper.pack_start(self._conferenceButton, False, True)

		self._magazineButton = self._create_button("magazines", "Magazines")
		#self._magazineButton.connect("clicked", self._on_source_selected)
		self._magazineWrapper = gtk.VBox()
		self._magazineWrapper.pack_start(self._magazineButton, False, True)

		self._scriptureButton = self._create_button("scriptures", "Scriptures")
		#self._scriptureButton.connect("clicked", self._on_source_selected)
		self._scriptureWrapper = gtk.VBox()
		self._scriptureWrapper.pack_start(self._scriptureButton, False, True)

		self._buttonLayout = gtk.VButtonBox()
		self._buttonLayout.set_layout(gtk.BUTTONBOX_SPREAD)
		self._buttonLayout.pack_start(self._radioWrapper, True, True)
		self._buttonLayout.pack_start(self._conferenceWrapper, True, True)
		self._buttonLayout.pack_start(self._magazineWrapper, True, True)
		self._buttonLayout.pack_start(self._scriptureWrapper, True, True)

		self._playcontrol = playcontrol.NavControl(player, store)

		self._layout.pack_start(self._loadingBanner.toplevel, False, False)
		self._layout.pack_start(self._buttonLayout, True, True)
		self._layout.pack_start(self._playcontrol.toplevel, False, True)

		self._window.set_title(constants.__pretty_app_name__)

	def show(self):
		BasicWindow.show(self)

		self._errorBanner.toplevel.hide()
		self._playcontrol.toplevel.hide()

		self._refresh()

	def _show_loading(self):
		animationPath = self._store.STORE_LOOKUP["loading"]
		animation = self._store.get_pixbuf_animation_from_store(animationPath)
		self._loadingBanner.show(animation, "Loading...")
		self._buttonLayout.set_sensitive(False)

	def _hide_loading(self):
		self._loadingBanner.hide()
		self._buttonLayout.set_sensitive(True)

	def _refresh(self):
		self._show_loading()
		self._index.get_languages(self._on_languages, self._on_error)

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
	def _on_languages(self, languages):
		self._hide_loading()
		self._languages = list(languages)

	@misc_utils.log_exception(_moduleLogger)
	def _on_error(self, exception):
		self._hide_loading()
		self._errorBanner.push_message(str(exception))

	@misc_utils.log_exception(_moduleLogger)
	def _on_source_selected(self, widget, Source, nodeName):
		node = self._index.get_source(nodeName, self._languages[0]["id"])
		sourceWindow = Source(self._player, self._store, node)
		sourceWindow.window.set_modal(True)
		sourceWindow.window.set_transient_for(self._window)
		sourceWindow.window.set_default_size(*self._window.get_size())
		sourceWindow.connect("quit", self._on_quit)
		sourceWindow.show()


gobject.type_register(SourceSelector)


class RadioWindow(BasicWindow):

	def __init__(self, player, store, node):
		BasicWindow.__init__(self, player, store)
		self._node = node
		self._childNode = None

		self._player.connect("state-change", self._on_player_state_change)
		self._player.connect("title-change", self._on_player_title_change)

		self._loadingBanner = banners.GenericBanner()

		headerPath = self._store.STORE_LOOKUP["radio_header"]
		self._header = self._store.get_image_from_store(headerPath)
		self._headerNavigation = presenter.NavigationBox()
		self._headerNavigation.toplevel.add(self._header)
		self._headerNavigation.connect("action", self._on_nav_action)
		self._headerNavigation.connect("navigating", self._on_navigating)

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
		self._treeView.get_selection().connect("changed", self._on_row_changed)

		self._treeScroller = gtk.ScrolledWindow()
		self._treeScroller.add(self._treeView)
		self._treeScroller.set_policy(gtk.POLICY_NEVER, gtk.POLICY_AUTOMATIC)

		self._presenter = presenter.StreamMiniPresenter(self._store)
		if self._player.state == "play":
			self._presenter.set_state(self._store.STORE_LOOKUP["play"])
		else:
			self._presenter.set_state(self._store.STORE_LOOKUP["pause"])
		self._presenterNavigation = presenter.NavigationBox()
		self._presenterNavigation.toplevel.add(self._presenter.toplevel)
		self._presenterNavigation.connect("action", self._on_nav_action)
		self._presenterNavigation.connect("navigating", self._on_navigating)

		self._radioLayout = gtk.VBox(False)
		self._radioLayout.pack_start(self._headerNavigation.toplevel, False, False)
		self._radioLayout.pack_start(self._treeScroller, True, True)
		self._radioLayout.pack_start(self._presenterNavigation.toplevel, False, True)

		self._layout.pack_start(self._loadingBanner.toplevel, False, False)
		self._layout.pack_start(self._radioLayout, True, True)

		self._window.set_title("Radio")
		self._dateShown = datetime.datetime.now()

	def show(self):
		BasicWindow.show(self)

		self._errorBanner.toplevel.hide()
		self._loadingBanner.toplevel.hide()

		self._refresh()

	def _show_loading(self):
		animationPath = self._store.STORE_LOOKUP["loading"]
		animation = self._store.get_pixbuf_animation_from_store(animationPath)
		self._loadingBanner.show(animation, "Loading...")

	def _hide_loading(self):
		self._loadingBanner.hide()

	def _refresh(self):
		self._show_loading()
		self._programmingModel.clear()
		self._node.get_children(
			self._on_channels,
			self._on_load_error,
		)

	def _get_current_row(self):
		nowTime = self._dateShown.strftime("%H:%M:%S")
		i = 0
		for i, row in enumerate(self._programmingModel):
			if nowTime < row[0]:
				if i == 0:
					return 0
				else:
					return i - 1
		else:
			return i

	@misc_utils.log_exception(_moduleLogger)
	def _on_player_state_change(self, player, newState):
		if self._headerNavigation.is_active() or self._presenterNavigation.is_active():
			return

		if newState == "play":
			self._presenter.set_state(self._store.STORE_LOOKUP["play"])
		elif newState == "pause":
			self._presenter.set_state(self._store.STORE_LOOKUP["pause"])
		else:
			_moduleLogger.info("Unhandled player state %s" % newState)
			self._presenter.set_state(self._store.STORE_LOOKUP["pause"])

	@misc_utils.log_exception(_moduleLogger)
	def _on_player_title_change(self, player, newState):
		_moduleLogger.info("Player title magically changed to %s" % player.title)
		self._destroy()

	@misc_utils.log_exception(_moduleLogger)
	def _on_navigating(self, widget, navState):
		if navState == "clicking":
			if self._player.state == "play":
				imageName = "pause"
			else:
				imageName = "play"
		elif navState == "down":
			imageName = "home"
		elif navState == "up":
			imageName = "play"
		elif navState == "left":
			imageName = "play"
		elif navState == "right":
			imageName = "play"

		self._presenter.set_state(self._store.STORE_LOOKUP[imageName])

	@misc_utils.log_exception(_moduleLogger)
	def _on_nav_action(self, widget, navState):
		if self._player.state == "play":
			self._presenter.set_state(self._store.STORE_LOOKUP["play"])
		else:
			self._presenter.set_state(self._store.STORE_LOOKUP["pause"])

		if navState == "clicking":
			if self._player.state == "play":
				self._player.pause()
			else:
				self._player.play()
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

		channels = channels
		if 1 < len(channels):
			_moduleLogger.warning("More channels now available!")
		self._childNode = channels[0]
		self._childNode.get_programming(
			self._dateShown,
			self._on_channel,
			self._on_load_error,
		)

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

	@misc_utils.log_exception(_moduleLogger)
	def _on_load_error(self, exception):
		self._hide_loading()
		self._errorBanner.push_message(str(exception))

	@misc_utils.log_exception(_moduleLogger)
	def _on_row_changed(self, selection):
		if len(self._programmingModel) == 0:
			return

		rowIndex = self._get_current_row()
		path = (rowIndex, )
		if not selection.path_is_selected(path):
			# Undo the user's changing of the selection
			selection.select_path(path)


gobject.type_register(RadioWindow)


class ListWindow(BasicWindow):

	def __init__(self, player, store, node):
		BasicWindow.__init__(self, player, store)
		self._node = node

		self._loadingBanner = banners.GenericBanner()

		modelTypes, columns = zip(*self._get_columns())

		self._model = gtk.ListStore(*modelTypes)

		self._treeView = gtk.TreeView()
		self._treeView.connect("row-activated", self._on_row_activated)
		self._treeView.set_headers_visible(False)
		self._treeView.set_model(self._model)
		for column in columns:
			if column is not None:
				self._treeView.append_column(column)

		self._treeScroller = gtk.ScrolledWindow()
		self._treeScroller.add(self._treeView)
		self._treeScroller.set_policy(gtk.POLICY_NEVER, gtk.POLICY_AUTOMATIC)

		self._separator = gtk.HSeparator()
		self._playcontrol = playcontrol.NavControl(self._player, self._store)
		self._playcontrol.connect("home", self._on_home)
		self._playcontrol.connect("jump-to", self._on_jump)

		self._contentLayout = gtk.VBox(False)
		self._contentLayout.pack_start(self._treeScroller, True, True)
		self._contentLayout.pack_start(self._separator, False, True)
		self._contentLayout.pack_start(self._playcontrol.toplevel, False, True)

		self._layout.pack_start(self._loadingBanner.toplevel, False, False)
		self._layout.pack_start(self._contentLayout, True, True)

	def show(self):
		BasicWindow.show(self)

		self._errorBanner.toplevel.hide()
		self._loadingBanner.toplevel.hide()

		self._refresh()
		self._playcontrol.refresh()

	@classmethod
	def _get_columns(cls):
		raise NotImplementedError("")

	def _get_current_row(self):
		raise NotImplementedError("")

	@misc_utils.log_exception(_moduleLogger)
	def _on_row_activated(self, view, path, column):
		raise NotImplementedError("")

	def _show_loading(self):
		animationPath = self._store.STORE_LOOKUP["loading"]
		animation = self._store.get_pixbuf_animation_from_store(animationPath)
		self._loadingBanner.show(animation, "Loading...")

	def _hide_loading(self):
		self._loadingBanner.hide()

	def _refresh(self):
		self._show_loading()
		self._model.clear()

	def _select_row(self):
		path = (self._get_current_row(), )
		self._treeView.scroll_to_cell(path)
		self._treeView.get_selection().select_path(path)


class ConferencesWindow(ListWindow):

	def __init__(self, player, store, node):
		ListWindow.__init__(self, player, store, node)
		self._window.set_title("Conferences")

	@classmethod
	def _get_columns(cls):
		yield gobject.TYPE_PYOBJECT, None

		textrenderer = gtk.CellRendererText()
		column = gtk.TreeViewColumn("Date")
		column.pack_start(textrenderer, expand=True)
		column.add_attribute(textrenderer, "text", 1)
		yield gobject.TYPE_STRING, column

		textrenderer = gtk.CellRendererText()
		column = gtk.TreeViewColumn("Conference")
		column.pack_start(textrenderer, expand=True)
		column.add_attribute(textrenderer, "text", 2)
		yield gobject.TYPE_STRING, column

	def _get_current_row(self):
		# @todo Not implemented yet
		return 0

	def _refresh(self):
		ListWindow._refresh(self)
		self._node.get_children(
			self._on_conferences,
			self._on_error,
		)

	@misc_utils.log_exception(_moduleLogger)
	def _on_conferences(self, programs):
		if self._isDestroyed:
			_moduleLogger.info("Download complete but window destroyed")
			return

		self._hide_loading()
		for programNode in programs:
			program = programNode.get_properties()
			row = programNode, program["title"], program["full_title"]
			self._model.append(row)

		path = (self._get_current_row(), )
		self._treeView.scroll_to_cell(path)
		self._treeView.get_selection().select_path(path)

	@misc_utils.log_exception(_moduleLogger)
	def _on_error(self, exception):
		self._hide_loading()
		self._errorBanner.push_message(str(exception))

	@misc_utils.log_exception(_moduleLogger)
	def _on_row_activated(self, view, path, column):
		itr = self._model.get_iter(path)
		node = self._model.get_value(itr, 0)

		sessionsWindow = ConferenceSessionsWindow(self._player, self._store, node)
		sessionsWindow.window.set_modal(True)
		sessionsWindow.window.set_transient_for(self._window)
		sessionsWindow.window.set_default_size(*self._window.get_size())
		sessionsWindow.connect("quit", self._on_quit)
		sessionsWindow.connect("home", self._on_home)
		sessionsWindow.show()


gobject.type_register(ConferencesWindow)


class ConferenceSessionsWindow(ListWindow):

	def __init__(self, player, store, node):
		ListWindow.__init__(self, player, store, node)
		self._window.set_title("Sessions")

	@classmethod
	def _get_columns(cls):
		yield gobject.TYPE_PYOBJECT, None

		textrenderer = gtk.CellRendererText()
		column = gtk.TreeViewColumn("Session")
		column.pack_start(textrenderer, expand=True)
		column.add_attribute(textrenderer, "text", 1)
		yield gobject.TYPE_STRING, column

	def _get_current_row(self):
		# @todo Not implemented yet
		return 0

	def _refresh(self):
		ListWindow._refresh(self)
		self._node.get_children(
			self._on_conference_sessions,
			self._on_error,
		)

	@misc_utils.log_exception(_moduleLogger)
	def _on_conference_sessions(self, programs):
		if self._isDestroyed:
			_moduleLogger.info("Download complete but window destroyed")
			return

		self._hide_loading()
		for programNode in programs:
			program = programNode.get_properties()
			row = programNode, program["title"]
			self._model.append(row)

		path = (self._get_current_row(), )
		self._treeView.scroll_to_cell(path)
		self._treeView.get_selection().select_path(path)

	@misc_utils.log_exception(_moduleLogger)
	def _on_error(self, exception):
		self._hide_loading()
		self._errorBanner.push_message(str(exception))

	@misc_utils.log_exception(_moduleLogger)
	def _on_row_activated(self, view, path, column):
		itr = self._model.get_iter(path)
		node = self._model.get_value(itr, 0)

		sessionsWindow = ConferenceTalksWindow(self._player, self._store, node)
		sessionsWindow.window.set_modal(True)
		sessionsWindow.window.set_transient_for(self._window)
		sessionsWindow.window.set_default_size(*self._window.get_size())
		sessionsWindow.connect("quit", self._on_quit)
		sessionsWindow.connect("home", self._on_home)
		sessionsWindow.show()


gobject.type_register(ConferenceSessionsWindow)


class ConferenceTalksWindow(ListWindow):

	def __init__(self, player, store, node):
		ListWindow.__init__(self, player, store, node)
		self._window.set_title("Talks")

	@classmethod
	def _get_columns(cls):
		yield gobject.TYPE_PYOBJECT, None

		textrenderer = gtk.CellRendererText()
		column = gtk.TreeViewColumn("Talk")
		column.pack_start(textrenderer, expand=True)
		column.add_attribute(textrenderer, "text", 1)
		yield gobject.TYPE_STRING, column

	def _get_current_row(self):
		# @todo Not implemented yet
		return 0

	def _refresh(self):
		ListWindow._refresh(self)
		self._node.get_children(
			self._on_conference_talks,
			self._on_error,
		)

	@misc_utils.log_exception(_moduleLogger)
	def _on_conference_talks(self, programs):
		if self._isDestroyed:
			_moduleLogger.info("Download complete but window destroyed")
			return

		self._hide_loading()
		for programNode in programs:
			program = programNode.get_properties()
			row = programNode, "%s\n%s" % (program["title"], program["speaker"])
			self._model.append(row)

		path = (self._get_current_row(), )
		self._treeView.scroll_to_cell(path)
		self._treeView.get_selection().select_path(path)

	@misc_utils.log_exception(_moduleLogger)
	def _on_error(self, exception):
		self._hide_loading()
		self._errorBanner.push_message(str(exception))

	@misc_utils.log_exception(_moduleLogger)
	def _on_row_activated(self, view, path, column):
		itr = self._model.get_iter(path)
		node = self._model.get_value(itr, 0)

		sessionsWindow = ConferenceTalkWindow(self._player, self._store, node)
		sessionsWindow.window.set_modal(True)
		sessionsWindow.window.set_transient_for(self._window)
		sessionsWindow.window.set_default_size(*self._window.get_size())
		sessionsWindow.connect("quit", self._on_quit)
		sessionsWindow.connect("home", self._on_home)
		sessionsWindow.show()


gobject.type_register(ConferenceTalksWindow)


class ConferenceTalkWindow(BasicWindow):

	def __init__(self, player, store, node):
		BasicWindow.__init__(self, player, store)

		self._player.connect("state-change", self._on_player_state_change)
		self._player.connect("title-change", self._on_player_title_change)

		self._loadingBanner = banners.GenericBanner()

		self._presenter = presenter.StreamPresenter(self._store)
		self._presenterNavigation = presenter.NavigationBox()
		self._presenterNavigation.toplevel.add(self._presenter.toplevel)
		self._presenterNavigation.connect("action", self._on_nav_action)
		self._presenterNavigation.connect("navigating", self._on_navigating)

		self._layout.pack_start(self._loadingBanner.toplevel, False, False)
		self._layout.pack_start(self._presenterNavigation.toplevel, True, True)

		self._window.set_title("Talk")

	def show(self):
		BasicWindow.show(self)
		self._window.show_all()
		self._errorBanner.toplevel.hide()
		self._loadingBanner.toplevel.hide()

		self._presenter.set_context(
			self._store.STORE_LOOKUP["conference_background"],
			self._player.title,
			self._player.subtitle,
		)
		if self._player.state == "play":
			self._presenter.set_state(self._store.STORE_LOOKUP["play"])
		else:
			self._presenter.set_state(self._store.STORE_LOOKUP["pause"])

	def _show_loading(self):
		animationPath = self._store.STORE_LOOKUP["loading"]
		animation = self._store.get_pixbuf_animation_from_store(animationPath)
		self._loadingBanner.show(animation, "Loading...")

	def _hide_loading(self):
		self._loadingBanner.hide()

	@misc_utils.log_exception(_moduleLogger)
	def _on_player_state_change(self, player, newState):
		if self._presenterNavigation.is_active():
			return

		if newState == "play":
			self._presenter.set_state(self._store.STORE_LOOKUP["play"])
		elif newState == "pause":
			self._presenter.set_state(self._store.STORE_LOOKUP["pause"])
		else:
			_moduleLogger.info("Unhandled player state %s" % newState)
			self._presenter.set_state(self._store.STORE_LOOKUP["pause"])

	@misc_utils.log_exception(_moduleLogger)
	def _on_player_title_change(self, player, newState):
		self._presenter.set_context(
			self._store.STORE_LOOKUP["conference_background"],
			self._player.title,
			self._player.subtitle,
		)

	@misc_utils.log_exception(_moduleLogger)
	def _on_navigating(self, widget, navState):
		if navState == "clicking":
			if self._player.state == "play":
				imageName = "pause"
			else:
				imageName = "play"
		elif navState == "down":
			imageName = "home"
		elif navState == "up":
			imageName = "play"
		elif navState == "left":
			imageName = "next"
		elif navState == "right":
			imageName = "prev"

		self._presenter.set_state(self._store.STORE_LOOKUP[imageName])

	@misc_utils.log_exception(_moduleLogger)
	def _on_nav_action(self, widget, navState):
		if self._player.state == "play":
			self._presenter.set_state(self._store.STORE_LOOKUP["play"])
		else:
			self._presenter.set_state(self._store.STORE_LOOKUP["pause"])

		if navState == "clicking":
			if self._player.state == "play":
				self._player.pause()
			else:
				self._player.play()
		elif navState == "down":
			self.emit("home")
			self._window.destroy()
		elif navState == "up":
			pass
		elif navState == "left":
			self._player.next()
		elif navState == "right":
			self._player.back()


gobject.type_register(ConferenceTalkWindow)
