from __future__ import with_statement

import ConfigParser
import logging

import gobject
import gtk

import constants
import hildonize
import util.misc as misc_utils
import util.go_utils as go_utils

import stream_index
import banners
import playcontrol


_moduleLogger = logging.getLogger(__name__)


class BasicWindow(gobject.GObject, go_utils.AutoSignal):

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

	def __init__(self, app, player, store):
		gobject.GObject.__init__(self)
		self._isDestroyed = False

		self._app = app
		self._player = player
		self._store = store

		self._clipboard = gtk.clipboard_get()
		self._windowInFullscreen = False

		self._errorBanner = banners.StackingBanner()

		self._layout = gtk.VBox()
		self._layout.pack_start(self._errorBanner.toplevel, False, True)

		self._window = gtk.Window()
		go_utils.AutoSignal.__init__(self, self.window)
		self._window.add(self._layout)
		self._window = hildonize.hildonize_window(self._app, self._window)

		self._window.set_icon(self._store.get_pixbuf_from_store(self._store.STORE_LOOKUP["icon"]))
		self._window.connect("key-press-event", self._on_key_press)
		self._window.connect("window-state-event", self._on_window_state_change)
		self._window.connect("destroy", self._on_destroy)

	@property
	def window(self):
		return self._window

	def show(self):
		hildonize.window_to_portrait(self._window)
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

	def jump_to(self, node):
		raise NotImplementedError("On %s" % self)

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
		raise NotImplementedError("On %s" % self)

	@misc_utils.log_exception(_moduleLogger)
	def _on_quit(self, *args):
		self.emit("quit")
		self._window.destroy()


class ListWindow(BasicWindow):

	def __init__(self, app, player, store, node):
		BasicWindow.__init__(self, app, player, store)
		self._node = node

		self.connect_auto(self._player, "title-change", self._on_player_title_change)

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
		if self._player.node is None:
			return -1
		ancestors, current, descendants = stream_index.common_paths(self._player.node, self._node)
		if not descendants:
			return -1
		activeChild = descendants[0]
		for i, row in enumerate(self._model):
			if activeChild is row[0]:
				return i
		else:
			return -1

	def jump_to(self, node):
		ancestors, current, descendants = stream_index.common_paths(node, self._node)
		if current is None:
			raise RuntimeError("Cannot jump to node %s" % node)
		if not descendants:
			_moduleLogger.info("Current node is the target")
			return
		child = descendants[0]
		window = self._window_from_node(child)
		window.jump_to(node)

	def _window_from_node(self, node):
		raise NotImplementedError("")

	@misc_utils.log_exception(_moduleLogger)
	def _on_row_activated(self, view, path, column):
		raise NotImplementedError("")

	@misc_utils.log_exception(_moduleLogger)
	def _on_player_title_change(self, player, node):
		self._select_row()

	@misc_utils.log_exception(_moduleLogger)
	def _on_jump(self, source, node):
		ancestors, current, descendants = stream_index.common_paths(node, self._node)
		if current is None:
			_moduleLogger.info("%s is not the target, moving up" % self._node)
			self.emit("jump-to", node)
			self._window.destroy()
			return
		if not descendants:
			_moduleLogger.info("Current node is the target")
			return
		child = descendants[0]
		window = self._window_from_node(child)
		window.jump_to(node)

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
		rowIndex = self._get_current_row()
		if rowIndex < 0:
			return
		path = (rowIndex, )
		self._treeView.scroll_to_cell(path)
		self._treeView.get_selection().select_path(path)
