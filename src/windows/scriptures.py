import logging

import gobject
import gtk

import hildonize
import util.go_utils as go_utils
import util.misc as misc_utils

import windows


_moduleLogger = logging.getLogger(__name__)


class ScripturesWindow(windows._base.ListWindow):

	def __init__(self, app, player, store, node):
		windows._base.ListWindow.__init__(self, app, player, store, node)
		self._window.set_title(self._node.title)

	@classmethod
	def _get_columns(cls):
		yield gobject.TYPE_PYOBJECT, None

		textrenderer = gtk.CellRendererText()
		hildonize.set_cell_thumb_selectable(textrenderer)
		column = gtk.TreeViewColumn("Scripture")
		column.set_property("sizing", gtk.TREE_VIEW_COLUMN_FIXED)
		column.pack_start(textrenderer, expand=True)
		column.add_attribute(textrenderer, "text", 1)
		yield gobject.TYPE_STRING, column

	def _refresh(self):
		windows._base.ListWindow._refresh(self)
		self._node.get_children(
			self._on_scriptures,
			self._on_error,
		)

	@misc_utils.log_exception(_moduleLogger)
	def _on_scriptures(self, programs):
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
		booksWindow = ScriptureBooksWindow(self._app, self._player, self._store, node)
		booksWindow.window.set_modal(True)
		booksWindow.window.set_transient_for(self._window)
		if self._windowInFullscreen:
			booksWindow.window.fullscreen()
		else:
			booksWindow.window.unfullscreen()
		booksWindow.connect_auto(booksWindow, "quit", self._on_quit)
		booksWindow.connect_auto(booksWindow, "home", self._on_home)
		booksWindow.connect_auto(booksWindow, "jump-to", self._on_jump)
		booksWindow.connect_auto(booksWindow, "fullscreen", self._on_child_fullscreen)
		booksWindow.show()
		return booksWindow


gobject.type_register(ScripturesWindow)


class ScriptureBooksWindow(windows._base.ListWindow):

	def __init__(self, app, player, store, node):
		windows._base.ListWindow.__init__(self, app, player, store, node)
		self._window.set_title(self._node.title)

	@classmethod
	def _get_columns(cls):
		yield gobject.TYPE_PYOBJECT, None

		textrenderer = gtk.CellRendererText()
		hildonize.set_cell_thumb_selectable(textrenderer)
		column = gtk.TreeViewColumn("Book")
		column.set_property("sizing", gtk.TREE_VIEW_COLUMN_FIXED)
		column.pack_start(textrenderer, expand=True)
		column.add_attribute(textrenderer, "text", 1)
		yield gobject.TYPE_STRING, column

	def _refresh(self):
		windows._base.ListWindow._refresh(self)
		self._node.get_children(
			self._on_scripture_books,
			self._on_error,
		)

	@misc_utils.log_exception(_moduleLogger)
	def _on_scripture_books(self, programs):
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
		booksWindow = ScriptureChaptersWindow(self._app, self._player, self._store, node)
		booksWindow.window.set_modal(True)
		booksWindow.window.set_transient_for(self._window)
		if self._windowInFullscreen:
			booksWindow.window.fullscreen()
		else:
			booksWindow.window.unfullscreen()
		booksWindow.connect_auto(booksWindow, "quit", self._on_quit)
		booksWindow.connect_auto(booksWindow, "home", self._on_home)
		booksWindow.connect_auto(booksWindow, "jump-to", self._on_jump)
		booksWindow.connect_auto(booksWindow, "fullscreen", self._on_child_fullscreen)
		booksWindow.show()
		return booksWindow


gobject.type_register(ScriptureBooksWindow)


class ScriptureChaptersWindow(windows._base.ListWindow):

	def __init__(self, app, player, store, node):
		windows._base.ListWindow.__init__(self, app, player, store, node)
		self._window.set_title(self._node.title)

	@classmethod
	def _get_columns(cls):
		yield gobject.TYPE_PYOBJECT, None

		textrenderer = gtk.CellRendererText()
		hildonize.set_cell_thumb_selectable(textrenderer)
		column = gtk.TreeViewColumn("Chapter")
		column.set_property("sizing", gtk.TREE_VIEW_COLUMN_FIXED)
		column.pack_start(textrenderer, expand=True)
		column.add_attribute(textrenderer, "text", 1)
		yield gobject.TYPE_STRING, column

	def _refresh(self):
		windows._base.ListWindow._refresh(self)
		self._node.get_children(
			self._on_scripture_chapters,
			self._on_error,
		)

	@misc_utils.log_exception(_moduleLogger)
	def _on_scripture_chapters(self, programs):
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
		booksWindow = ScriptureChapterWindow(self._app, self._player, self._store, node)
		booksWindow.window.set_modal(True)
		booksWindow.window.set_transient_for(self._window)
		if self._windowInFullscreen:
			booksWindow.window.fullscreen()
		else:
			booksWindow.window.unfullscreen()
		booksWindow.connect_auto(booksWindow, "quit", self._on_quit)
		booksWindow.connect_auto(booksWindow, "home", self._on_home)
		booksWindow.connect_auto(booksWindow, "jump-to", self._on_jump)
		booksWindow.connect_auto(booksWindow, "fullscreen", self._on_child_fullscreen)
		booksWindow.show()
		return booksWindow


gobject.type_register(ScriptureChaptersWindow)


class ScriptureChapterWindow(windows._base.PresenterWindow):

	def __init__(self, app, player, store, node):
		windows._base.PresenterWindow.__init__(self, app, player, store, node)

	def _get_background(self):
		return self._store.STORE_LOOKUP["scripture_background"]


gobject.type_register(ScriptureChapterWindow)
