import datetime
import logging

import gobject
import gtk

import hildonize
import util.misc as misc_utils
import banners
import presenter

import windows


_moduleLogger = logging.getLogger(__name__)


class RadioWindow(windows._base.BasicWindow):

	def __init__(self, app, player, store, node):
		windows._base.BasicWindow.__init__(self, app, player, store)
		self._node = node
		self._childNode = None

		self.connect_auto(self._player, "state-change", self._on_player_state_change)
		self.connect_auto(self._player, "title-change", self._on_player_title_change)

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
		timeColumn.set_property("sizing", gtk.TREE_VIEW_COLUMN_FIXED)
		timeColumn.set_property("fixed-width", 80)
		timeColumn.pack_start(textrenderer, expand=True)
		timeColumn.add_attribute(textrenderer, "text", 0)

		textrenderer = gtk.CellRendererText()
		hildonize.set_cell_thumb_selectable(textrenderer)
		titleColumn = gtk.TreeViewColumn("Program")
		titleColumn.set_property("sizing", gtk.TREE_VIEW_COLUMN_FIXED)
		titleColumn.pack_start(textrenderer, expand=True)
		titleColumn.add_attribute(textrenderer, "text", 1)

		self._treeView = gtk.TreeView()
		self._treeView.set_property("fixed-height-mode", True)
		self._treeView.set_headers_visible(False)
		self._treeView.set_model(self._programmingModel)
		self._treeView.append_column(timeColumn)
		self._treeView.append_column(titleColumn)
		self._treeView.get_selection().connect("changed", self._on_row_changed)

		self._treeScroller = gtk.ScrolledWindow()
		self._treeScroller.add(self._treeView)
		self._treeScroller.set_policy(gtk.POLICY_NEVER, gtk.POLICY_AUTOMATIC)

		self._presenter = presenter.StreamMiniPresenter(self._store)
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

		self._dateShown = datetime.datetime.now()
		self._update_title()

	def show(self):
		windows._base.BasicWindow.show(self)

		self._errorBanner.toplevel.hide()
		self._loadingBanner.toplevel.hide()

		self._refresh()

	def jump_to(self, node):
		_moduleLogger.info("Only 1 channel, nothing to jump to")

	def _update_title(self):
		self._window.set_title("%s - %s" % (self._node.title, self._dateShown.strftime("%m/%d")))

	@property
	def _active(self):
		return self._player.node is self._childNode

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
			self._presenter.set_state(self._store.STORE_LOOKUP["play"])

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
		self._set_context(self._player.state)

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

		self._set_context(newState)

	@misc_utils.log_exception(_moduleLogger)
	def _on_player_title_change(self, player, node):
		if node is not self._childNode or node is None:
			_moduleLogger.info("Player title magically changed to %s" % player.title)
			return

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
				imageName = "play_pressed"
				_moduleLogger.info("Unhandled player state %s" % self._player.state)
		elif navState == "down":
			imageName = "home"
		else:
			if self._player.state == self._player.STATE_PLAY:
				imageName = "pause"
			else:
				imageName = "play"

		self._presenter.set_state(self._store.STORE_LOOKUP[imageName])

	@misc_utils.log_exception(_moduleLogger)
	def _on_nav_action(self, widget, navState):
		self._set_context(self._player.state)

		if navState == "clicking":
			if self._player.state == self._player.STATE_PLAY:
				if self._active:
					self._player.pause()
				else:
					self._player.set_piece_by_node(self._childNode)
					self._player.play()
			elif self._player.state == self._player.STATE_PAUSE:
				self._player.play()
			elif self._player.state == self._player.STATE_STOP:
				self._player.set_piece_by_node(self._childNode)
				self._player.play()
			else:
				_moduleLogger.info("Unhandled player state %s" % self._player.state)
		elif navState == "down":
			self.window.destroy()
		elif navState == "up":
			pass
		elif navState == "left":
			self._dateShown += datetime.timedelta(days=1)
			self._update_title()
			self._refresh()
		elif navState == "right":
			self._dateShown -= datetime.timedelta(days=1)
			self._update_title()
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

		currentDate = datetime.datetime.now()
		if currentDate.date() != self._dateShown.date():
			self._treeView.get_selection().set_mode(gtk.SELECTION_NONE)
		else:
			self._treeView.get_selection().set_mode(gtk.SELECTION_SINGLE)
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
