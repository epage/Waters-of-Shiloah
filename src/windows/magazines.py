import logging

import gobject
import gtk

import hildonize
import util.go_utils as go_utils
import util.misc as misc_utils
import banners
import presenter
import stream_index

import windows


_moduleLogger = logging.getLogger(__name__)


class MagazinesWindow(windows._base.ListWindow):

	def __init__(self, player, store, node):
		windows._base.ListWindow.__init__(self, player, store, node)
		self._window.set_title(self._node.title)

	@classmethod
	def _get_columns(cls):
		yield gobject.TYPE_PYOBJECT, None

		pixrenderer = gtk.CellRendererPixbuf()
		column = gtk.TreeViewColumn("Covers")
		column.pack_start(pixrenderer, expand=True)
		column.add_attribute(pixrenderer, "pixbuf", 1)
		yield gobject.TYPE_OBJECT, column

		textrenderer = gtk.CellRendererText()
		column = gtk.TreeViewColumn("Magazine")
		column.pack_start(textrenderer, expand=True)
		column.add_attribute(textrenderer, "text", 2)
		yield gobject.TYPE_STRING, column

	def _refresh(self):
		windows._base.ListWindow._refresh(self)
		self._node.get_children(
			self._on_magazines,
			self._on_error,
		)

	@misc_utils.log_exception(_moduleLogger)
	def _on_magazines(self, programs):
		if self._isDestroyed:
			_moduleLogger.info("Download complete but window destroyed")
			return

		self._hide_loading()
		for programNode in programs:
			program = programNode.get_properties()
			img = self._store.get_pixbuf_from_store(self._store.STORE_LOOKUP["nomagazineimage"])
			row = programNode, img, program["title"]
			self._model.append(row)

		self._select_row()

	@misc_utils.log_exception(_moduleLogger)
	def _on_error(self, exception):
		self._hide_loading()
		self._errorBanner.push_message(str(exception))

	def _window_from_node(self, node):
		issuesWindow = MagazineIssuesWindow(self._player, self._store, node)
		issuesWindow.window.set_modal(True)
		issuesWindow.window.set_transient_for(self._window)
		issuesWindow.window.set_default_size(*self._window.get_size())
		issuesWindow.connect("quit", self._on_quit)
		issuesWindow.connect("home", self._on_home)
		issuesWindow.connect("jump-to", self._on_jump)
		issuesWindow.show()
		return issuesWindow

	@misc_utils.log_exception(_moduleLogger)
	def _on_row_activated(self, view, path, column):
		itr = self._model.get_iter(path)
		node = self._model.get_value(itr, 0)
		self._window_from_node(node)


gobject.type_register(MagazinesWindow)


class MagazineIssuesWindow(windows._base.ListWindow):

	def __init__(self, player, store, node):
		windows._base.ListWindow.__init__(self, player, store, node)
		self._window.set_title(self._node.title)

	@classmethod
	def _get_columns(cls):
		yield gobject.TYPE_PYOBJECT, None

		pixrenderer = gtk.CellRendererPixbuf()
		column = gtk.TreeViewColumn("Covers")
		column.pack_start(pixrenderer, expand=True)
		column.add_attribute(pixrenderer, "pixbuf", 1)
		yield gobject.TYPE_OBJECT, column

		textrenderer = gtk.CellRendererText()
		column = gtk.TreeViewColumn("Issue")
		column.pack_start(textrenderer, expand=True)
		column.add_attribute(textrenderer, "text", 2)
		yield gobject.TYPE_STRING, column

	def _refresh(self):
		windows._base.ListWindow._refresh(self)
		self._node.get_children(
			self._on_magazine_issues,
			self._on_error,
		)

	@misc_utils.log_exception(_moduleLogger)
	def _on_magazine_issues(self, programs):
		if self._isDestroyed:
			_moduleLogger.info("Download complete but window destroyed")
			return

		self._hide_loading()
		for programNode in programs:
			program = programNode.get_properties()
			img = self._store.get_pixbuf_from_store(self._store.STORE_LOOKUP["nomagazineimage"])
			row = programNode, img, program["title"]
			self._model.append(row)

		self._select_row()

	@misc_utils.log_exception(_moduleLogger)
	def _on_error(self, exception):
		self._hide_loading()
		self._errorBanner.push_message(str(exception))

	def _window_from_node(self, node):
		issuesWindow = MagazineArticlesWindow(self._player, self._store, node)
		issuesWindow.window.set_modal(True)
		issuesWindow.window.set_transient_for(self._window)
		issuesWindow.window.set_default_size(*self._window.get_size())
		issuesWindow.connect("quit", self._on_quit)
		issuesWindow.connect("home", self._on_home)
		issuesWindow.connect("jump-to", self._on_jump)
		issuesWindow.show()
		return issuesWindow

	@misc_utils.log_exception(_moduleLogger)
	def _on_row_activated(self, view, path, column):
		itr = self._model.get_iter(path)
		node = self._model.get_value(itr, 0)
		self._window_from_node(node)


gobject.type_register(MagazineIssuesWindow)


class MagazineArticlesWindow(windows._base.ListWindow):

	def __init__(self, player, store, node):
		windows._base.ListWindow.__init__(self, player, store, node)
		self._window.set_title(self._node.title)

	@classmethod
	def _get_columns(cls):
		yield gobject.TYPE_PYOBJECT, None

		textrenderer = gtk.CellRendererText()
		column = gtk.TreeViewColumn("Article")
		column.pack_start(textrenderer, expand=True)
		column.add_attribute(textrenderer, "text", 1)
		yield gobject.TYPE_STRING, column

	def _refresh(self):
		windows._base.ListWindow._refresh(self)
		self._node.get_children(
			self._on_magazine_articles,
			self._on_error,
		)

	@misc_utils.log_exception(_moduleLogger)
	def _on_magazine_articles(self, programs):
		if self._isDestroyed:
			_moduleLogger.info("Download complete but window destroyed")
			return

		self._hide_loading()
		for programNode in programs:
			program = programNode.get_properties()
			row = programNode, "%s\n%s" % (program["title"], program["author"])
			self._model.append(row)

		self._select_row()

	@misc_utils.log_exception(_moduleLogger)
	def _on_error(self, exception):
		self._hide_loading()
		self._errorBanner.push_message(str(exception))

	def _window_from_node(self, node):
		issuesWindow = MagazineArticleWindow(self._player, self._store, node)
		issuesWindow.window.set_modal(True)
		issuesWindow.window.set_transient_for(self._window)
		issuesWindow.window.set_default_size(*self._window.get_size())
		issuesWindow.connect("quit", self._on_quit)
		issuesWindow.connect("home", self._on_home)
		issuesWindow.connect("jump-to", self._on_jump)
		issuesWindow.show()
		return issuesWindow

	@misc_utils.log_exception(_moduleLogger)
	def _on_row_activated(self, view, path, column):
		itr = self._model.get_iter(path)
		node = self._model.get_value(itr, 0)
		self._window_from_node(node)


gobject.type_register(MagazineArticlesWindow)


class MagazineArticleWindow(windows._base.BasicWindow):

	def __init__(self, player, store, node):
		windows._base.BasicWindow.__init__(self, player, store)
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
			self._store.STORE_LOOKUP["magazine_background"],
			self._node.title,
			self._node.subtitle,
		)
		self._presenterNavigation = presenter.NavigationBox()
		self._presenterNavigation.toplevel.add(self._presenter.toplevel)
		self._presenterNavigation.connect("action", self._on_nav_action)
		self._presenterNavigation.connect("navigating", self._on_navigating)

		self._seekbar = hildonize.create_seekbar()
		self._seekbar.connect("change-value", self._on_user_seek)

		self._layout.pack_start(self._loadingBanner.toplevel, False, False)
		self._layout.pack_start(self._presenterNavigation.toplevel, True, True)
		self._layout.pack_start(self._seekbar, False, False)

		self._window.set_title(self._node.title)

	def show(self):
		windows._base.BasicWindow.show(self)
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
		self._seekbar.set_value(self._player.percent_elapsed * 100)
		return True if not self._isDestroyed else False

	@misc_utils.log_exception(_moduleLogger)
	def _on_player_state_change(self, player, newState):
		if self._active and self._player.state == self._player.STATE_PLAY:
			self._seekbar.show()
			assert self._updateSeek is None
			self._updateSeek = go_utils.Timeout(self._on_player_update_seek, once=False)
			self._updateSeek.start(seconds=1)
		else:
			self._seekbar.hide()
			self._updateSeek.cancel()
			self._updateSeek = None

		if not self._presenterNavigation.is_active():
			self._set_context(newState)

	@misc_utils.log_exception(_moduleLogger)
	def _on_player_title_change(self, player, node):
		if not self._active or node in [None, self._node]:
			self._playerNode = player.node
			return
		self._playerNode = player.node
		self.emit("jump-to", node)
		self._window.destroy()

	@misc_utils.log_exception(_moduleLogger)
	def _on_player_error(self, player, err, debug):
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


gobject.type_register(MagazineArticleWindow)
