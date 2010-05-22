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
import presenter


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
		self._window.add(self._layout)
		self._window = hildonize.hildonize_window(self._app, self._window)
		go_utils.AutoSignal.__init__(self, self.window)

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
			windowInFullscreen = config.getboolean(sectionName, "fullscreen")
		except ConfigParser.NoSectionError, e:
			_moduleLogger.info(
				"Settings file %s is missing section %s" % (
					constants._user_settings_,
					e.section,
				)
			)

		if windowInFullscreen:
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
		oldIsFull = self._windowInFullscreen
		if event.new_window_state & gtk.gdk.WINDOW_STATE_FULLSCREEN:
			self._windowInFullscreen = True
		else:
			self._windowInFullscreen = False
		if oldIsFull != self._windowInFullscreen:
			_moduleLogger.info("%r Emit fullscreen %s" % (self, self._windowInFullscreen))
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
			self._window.destroy()
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
	def _on_child_fullscreen(self, source, isFull):
		if isFull:
			_moduleLogger.info("Full screen %r to mirror child %r" % (self, source))
			self._window.fullscreen()
		else:
			_moduleLogger.info("Unfull screen %r to mirror child %r" % (self, source))
			self._window.unfullscreen()

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
		self._treeView.set_property("fixed-height-mode", True)
		self._treeView.set_headers_visible(False)
		self._treeView.set_model(self._model)
		for column in columns:
			if column is not None:
				self._treeView.append_column(column)

		self._viewport = gtk.Viewport()
		self._viewport.add(self._treeView)

		self._treeScroller = gtk.ScrolledWindow()
		self._treeScroller.add(self._viewport)
		self._treeScroller.set_policy(gtk.POLICY_NEVER, gtk.POLICY_AUTOMATIC)
		self._treeScroller = hildonize.hildonize_scrollwindow(self._treeScroller)

		self._separator = gtk.HSeparator()
		self._presenter = presenter.NavControl(self._player, self._store)
		self.connect_auto(self._presenter, "home", self._on_home)
		self.connect_auto(self._presenter, "jump-to", self._on_jump)

		self._contentLayout = gtk.VBox(False)
		self._contentLayout.pack_start(self._treeScroller, True, True)
		self._contentLayout.pack_start(self._separator, False, True)
		self._contentLayout.pack_start(self._presenter.toplevel, False, True)

		self._layout.pack_start(self._loadingBanner.toplevel, False, False)
		self._layout.pack_start(self._contentLayout, True, True)

	def show(self):
		BasicWindow.show(self)

		self._errorBanner.toplevel.hide()
		self._loadingBanner.toplevel.hide()

		self._refresh()
		self._presenter.refresh()

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
		itr = self._model.get_iter(path)
		node = self._model.get_value(itr, 0)
		self._window_from_node(node)

	@misc_utils.log_exception(_moduleLogger)
	def _on_player_title_change(self, player, node):
		assert not self._isDestroyed
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

	@misc_utils.log_exception(_moduleLogger)
	def _on_delay_scroll(self, *args):
		self._scroll_to_row()

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
		self._treeView.get_selection().select_path(path)

	def _scroll_to_row(self):
		rowIndex = self._get_current_row()
		if rowIndex < 0:
			return

		path = (rowIndex, )
		self._treeView.scroll_to_cell(path)

		treeViewHeight = self._treeView.get_allocation().height
		viewportHeight = self._viewport.get_allocation().height

		viewsPerPort = treeViewHeight / float(viewportHeight)
		maxRows = len(self._model)
		percentThrough = rowIndex / float(maxRows)
		dxByIndex = int(viewsPerPort * percentThrough * viewportHeight)

		dxMax = max(treeViewHeight - viewportHeight, 0)

		dx = min(dxByIndex, dxMax)
		adjustment = self._treeScroller.get_vadjustment()
		adjustment.value = dx


class PresenterWindow(BasicWindow):

	def __init__(self, app, player, store, node):
		BasicWindow.__init__(self, app, player, store)
		self._node = node
		self._playerNode = self._player.node
		self._nextSearch = None
		self._updateSeek = None

		self.connect_auto(self._player, "state-change", self._on_player_state_change)
		self.connect_auto(self._player, "title-change", self._on_player_title_change)
		self.connect_auto(self._player, "error", self._on_player_error)

		self._loadingBanner = banners.GenericBanner()

		self._presenter = presenter.StreamPresenter(self._store)
		self._presenter.set_context(
			self._get_background(),
			self._node.title,
			self._node.subtitle,
		)
		self._presenterNavigation = presenter.NavigationBox()
		self._presenterNavigation.toplevel.add(self._presenter.toplevel)
		self.connect_auto(self._presenterNavigation, "action", self._on_nav_action)
		self.connect_auto(self._presenterNavigation, "navigating", self._on_navigating)

		self._seekbar = hildonize.create_seekbar()
		self._seekbar.connect("change-value", self._on_user_seek)

		self._layout.pack_start(self._loadingBanner.toplevel, False, False)
		self._layout.pack_start(self._presenterNavigation.toplevel, True, True)
		self._layout.pack_start(self._seekbar, False, False)

		self._window.set_title(self._node.title)

	def _get_background(self):
		raise NotImplementedError()

	def show(self):
		BasicWindow.show(self)
		self._window.show_all()
		self._errorBanner.toplevel.hide()
		self._loadingBanner.toplevel.hide()
		self._set_context(self._player.state)
		self._seekbar.hide()

	def jump_to(self, node):
		assert self._node is node

	@property
	def _active(self):
		return self._playerNode is self._node

	def _show_loading(self):
		animationPath = self._store.STORE_LOOKUP["loading"]
		animation = self._store.get_pixbuf_animation_from_store(animationPath)
		self._loadingBanner.show(animation, "Loading...")

	def _hide_loading(self):
		self._loadingBanner.hide()

	def _set_context(self, state):
		if state == self._player.STATE_PLAY:
			if self._active:
				self._presenter.set_state(self._store.STORE_LOOKUP["pause"])
			else:
				self._presenter.set_state(self._store.STORE_LOOKUP["play"])
		elif state == self._player.STATE_PAUSE:
			self._presenter.set_state(self._store.STORE_LOOKUP["play"])
		elif state == self._player.STATE_STOP:
			self._presenter.set_state(self._store.STORE_LOOKUP["play"])
		else:
			_moduleLogger.info("Unhandled player state %s" % state)

	@misc_utils.log_exception(_moduleLogger)
	def _on_user_seek(self, widget, scroll, value):
		self._player.seek(value / 100.0)

	@misc_utils.log_exception(_moduleLogger)
	def _on_player_update_seek(self):
		if self._isDestroyed:
			return False
		self._seekbar.set_value(self._player.percent_elapsed * 100)
		return True

	@misc_utils.log_exception(_moduleLogger)
	def _on_player_state_change(self, player, newState):
		assert not self._isDestroyed
		if self._active and self._player.state == self._player.STATE_PLAY:
			self._seekbar.show()
			assert self._updateSeek is None
			self._updateSeek = go_utils.Timeout(self._on_player_update_seek, once=False)
			self._updateSeek.start(seconds=1)
		else:
			self._seekbar.hide()
			if self._updateSeek is not None:
				self._updateSeek.cancel()
				self._updateSeek = None

		if not self._presenterNavigation.is_active():
			self._set_context(newState)

	@misc_utils.log_exception(_moduleLogger)
	def _on_player_title_change(self, player, node):
		assert not self._isDestroyed
		if not self._active or node in [None, self._node]:
			self._playerNode = node
			return
		self._playerNode = node
		self.emit("jump-to", node)
		self._window.destroy()

	@misc_utils.log_exception(_moduleLogger)
	def _on_player_error(self, player, err, debug):
		assert not self._isDestroyed
		_moduleLogger.error("%r - %r" % (err, debug))

	@misc_utils.log_exception(_moduleLogger)
	def _on_navigating(self, widget, navState):
		if navState == "clicking":
			if self._player.state == self._player.STATE_PLAY:
				if self._active:
					imageName = "pause_pressed"
				else:
					imageName = "play_pressed"
			elif self._player.state == self._player.STATE_PAUSE:
				imageName = "play_pressed"
			elif self._player.state == self._player.STATE_STOP:
				imageName = "play_pressed"
			else:
				_moduleLogger.info("Unhandled player state %s" % self._player.state)
		elif navState == "down":
			imageName = "home"
		elif navState == "up":
			if self._player.state == self._player.STATE_PLAY:
				if self._active:
					imageName = "pause"
				else:
					imageName = "play"
			elif self._player.state == self._player.STATE_PAUSE:
				imageName = "play"
			elif self._player.state == self._player.STATE_STOP:
				imageName = "play"
			else:
				_moduleLogger.info("Unhandled player state %s" % self._player.state)
		elif navState == "left":
			imageName = "next"
		elif navState == "right":
			imageName = "prev"

		self._presenter.set_state(self._store.STORE_LOOKUP[imageName])

	@misc_utils.log_exception(_moduleLogger)
	def _on_nav_action(self, widget, navState):
		self._set_context(self._player.state)

		if navState == "clicking":
			if self._player.state == self._player.STATE_PLAY:
				if self._active:
					self._player.pause()
				else:
					self._player.set_piece_by_node(self._node)
					self._player.play()
			elif self._player.state == self._player.STATE_PAUSE:
				self._player.play()
			elif self._player.state == self._player.STATE_STOP:
				self._player.set_piece_by_node(self._node)
				self._player.play()
			else:
				_moduleLogger.info("Unhandled player state %s" % self._player.state)
		elif navState == "down":
			self.emit("home")
			self._window.destroy()
		elif navState == "up":
			pass
		elif navState == "left":
			if self._active:
				self._player.next()
			else:
				assert self._nextSearch is None
				self._nextSearch = stream_index.AsyncWalker(stream_index.get_next)
				self._nextSearch.start(self._node, self._on_next_node, self._on_node_search_error)
		elif navState == "right":
			if self._active:
				self._player.back()
			else:
				assert self._nextSearch is None
				self._nextSearch = stream_index.AsyncWalker(stream_index.get_previous)
				self._nextSearch.start(self._node, self._on_next_node, self._on_node_search_error)

	@misc_utils.log_exception(_moduleLogger)
	def _on_next_node(self, node):
		self._nextSearch = None
		self.emit("jump-to", node)
		self._window.destroy()

	@misc_utils.log_exception(_moduleLogger)
	def _on_node_search_error(self, e):
		self._nextSearch = None
		self._errorBanner.push_message(str(e))
