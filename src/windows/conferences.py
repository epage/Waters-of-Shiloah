import logging

import gobject
import gtk

import hildonize
import util.go_utils as go_utils
import util.misc as misc_utils
import banners
import stream_index

import windows


_moduleLogger = logging.getLogger(__name__)


class ConferencesWindow(windows._base.ListWindow):

	def __init__(self, app, player, store, node):
		windows._base.ListWindow.__init__(self, app, player, store, node)
		self._window.set_title(self._node.title)

	@classmethod
	def _get_columns(cls):
		yield gobject.TYPE_PYOBJECT, None

		textrenderer = gtk.CellRendererText()
		textrenderer.set_property("scale", 0.75)
		column = gtk.TreeViewColumn("Date")
		column.set_property("sizing", gtk.TREE_VIEW_COLUMN_FIXED)
		column.set_property("fixed-width", 96)
		column.pack_start(textrenderer, expand=True)
		column.add_attribute(textrenderer, "text", 1)
		yield gobject.TYPE_STRING, column

		textrenderer = gtk.CellRendererText()
		hildonize.set_cell_thumb_selectable(textrenderer)
		column = gtk.TreeViewColumn("Conference")
		column.set_property("sizing", gtk.TREE_VIEW_COLUMN_FIXED)
		column.pack_start(textrenderer, expand=True)
		column.add_attribute(textrenderer, "text", 2)
		yield gobject.TYPE_STRING, column

	def _refresh(self):
		windows._base.ListWindow._refresh(self)
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

		self._select_row()
		go_utils.Async(self._on_delay_scroll).start()

	@misc_utils.log_exception(_moduleLogger)
	def _on_error(self, exception):
		self._hide_loading()
		self._errorBanner.push_message(str(exception))

	def _window_from_node(self, node):
		sessionsWindow = ConferenceSessionsWindow(self._app, self._player, self._store, node)
		sessionsWindow.window.set_modal(True)
		sessionsWindow.window.set_transient_for(self._window)
		sessionsWindow.window.set_default_size(*self._window.get_size())
		sessionsWindow.connect("quit", self._on_quit)
		sessionsWindow.connect("home", self._on_home)
		sessionsWindow.connect("jump-to", self._on_jump)
		sessionsWindow.show()
		return sessionsWindow


gobject.type_register(ConferencesWindow)


class ConferenceSessionsWindow(windows._base.ListWindow):

	def __init__(self, app, player, store, node):
		windows._base.ListWindow.__init__(self, app, player, store, node)
		self._window.set_title(self._node.title)

	@classmethod
	def _get_columns(cls):
		yield gobject.TYPE_PYOBJECT, None

		textrenderer = gtk.CellRendererText()
		hildonize.set_cell_thumb_selectable(textrenderer)
		column = gtk.TreeViewColumn("Session")
		column.set_property("sizing", gtk.TREE_VIEW_COLUMN_FIXED)
		column.pack_start(textrenderer, expand=True)
		column.add_attribute(textrenderer, "text", 1)
		yield gobject.TYPE_STRING, column

	def _refresh(self):
		windows._base.ListWindow._refresh(self)
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

		self._select_row()
		go_utils.Async(self._on_delay_scroll).start()

	@misc_utils.log_exception(_moduleLogger)
	def _on_error(self, exception):
		self._hide_loading()
		self._errorBanner.push_message(str(exception))

	def _window_from_node(self, node):
		sessionsWindow = ConferenceTalksWindow(self._app, self._player, self._store, node)
		sessionsWindow.window.set_modal(True)
		sessionsWindow.window.set_transient_for(self._window)
		sessionsWindow.window.set_default_size(*self._window.get_size())
		sessionsWindow.connect("quit", self._on_quit)
		sessionsWindow.connect("home", self._on_home)
		sessionsWindow.connect("jump-to", self._on_jump)
		sessionsWindow.show()
		return sessionsWindow


gobject.type_register(ConferenceSessionsWindow)


class ConferenceTalksWindow(windows._base.ListWindow):

	def __init__(self, app, player, store, node):
		windows._base.ListWindow.__init__(self, app, player, store, node)
		self._window.set_title(self._node.title)

	@classmethod
	def _get_columns(cls):
		yield gobject.TYPE_PYOBJECT, None

		textrenderer = gtk.CellRendererText()
		column = gtk.TreeViewColumn("Talk")
		column.set_property("sizing", gtk.TREE_VIEW_COLUMN_FIXED)
		column.pack_start(textrenderer, expand=True)
		column.add_attribute(textrenderer, "markup", 1)
		yield gobject.TYPE_STRING, column

	def _refresh(self):
		windows._base.ListWindow._refresh(self)
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
			row = programNode, "%s\n<small>%s</small>" % (programNode.title, programNode.subtitle)
			self._model.append(row)

		self._select_row()
		go_utils.Async(self._on_delay_scroll).start()

	@misc_utils.log_exception(_moduleLogger)
	def _on_error(self, exception):
		self._hide_loading()
		self._errorBanner.push_message(str(exception))

	def _window_from_node(self, node):
		sessionsWindow = ConferenceTalkWindow(self._app, self._player, self._store, node)
		sessionsWindow.window.set_modal(True)
		sessionsWindow.window.set_transient_for(self._window)
		sessionsWindow.window.set_default_size(*self._window.get_size())
		sessionsWindow.connect("quit", self._on_quit)
		sessionsWindow.connect("home", self._on_home)
		sessionsWindow.connect("jump-to", self._on_jump)
		sessionsWindow.show()
		return sessionsWindow


gobject.type_register(ConferenceTalksWindow)


class ConferenceTalkWindow(windows._base.PresenterWindow):

	def __init__(self, app, player, store, node):
		windows._base.PresenterWindow.__init__(self, app, player, store, node)

	def _get_background(self):
		return self._store.STORE_LOOKUP["conference_background"]


gobject.type_register(ConferenceTalkWindow)
