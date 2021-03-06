import datetime
import logging

import gobject
import gtk

import hildonize
import util.misc as misc_utils
import util.time_utils as time_utils
import util.go_utils as go_utils
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

		self._programmingModel = gtk.ListStore(
			gobject.TYPE_STRING,
			gobject.TYPE_STRING,
		)

		textrenderer = gtk.CellRendererText()
		timeColumn = gtk.TreeViewColumn("Time")
		textrenderer.set_property("scale", 0.75)
		timeColumn.set_property("sizing", gtk.TREE_VIEW_COLUMN_FIXED)
		timeColumn.set_property("fixed-width", 80)
		timeColumn.pack_start(textrenderer, expand=True)
		timeColumn.add_attribute(textrenderer, "text", 0)

		textrenderer = gtk.CellRendererText()
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

		self._viewport = gtk.Viewport()
		self._viewport.add(self._treeView)

		self._treeScroller = gtk.ScrolledWindow()
		self._treeScroller.add(self._viewport)
		self._treeScroller.set_policy(gtk.POLICY_NEVER, gtk.POLICY_AUTOMATIC)
		self._treeScroller = hildonize.hildonize_scrollwindow(self._treeScroller)

		self._presenter = presenter.StreamMiniPresenter(self._store)
		self._presenterNavigation = presenter.NavigationBox()
		self._presenterNavigation.toplevel.add(self._presenter.toplevel)
		self.connect_auto(self._presenterNavigation, "action", self._on_nav_action)
		self.connect_auto(self._presenterNavigation, "navigating", self._on_navigating)
		self.connect_auto(self._player, "error", self._on_player_error)

		self._radioLayout = gtk.VBox(False)
		self._radioLayout.pack_start(self._treeScroller, True, True)
		self._radioLayout.pack_start(self._presenterNavigation.toplevel, False, True)

		self._layout.pack_start(self._loadingBanner.toplevel, False, False)
		self._layout.pack_start(self._radioLayout, True, True)

		self._dateShown = datetime.datetime.now(tz=time_utils.Mountain)
		self._currentTime = self._dateShown
		self._update_title()

		self._continualUpdate = go_utils.Timeout(self._on_continual_update, once = False)
		self._continualUpdate.start(seconds=60)

	def show(self):
		windows._base.BasicWindow.show(self)

		self._errorBanner.toplevel.hide()
		self._loadingBanner.toplevel.hide()

		self._refresh()

	def jump_to(self, node):
		_moduleLogger.info("Only 1 channel, nothing to jump to")

	def _update_time(self, newTime):
		oldTime = self._dateShown
		self._dateShown = newTime
		if newTime.date() == oldTime.date():
			self._select_row()
		else:
			self._update_title()
			self._refresh()

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
	def _on_player_error(self, player, err, debug):
		assert not self._isDestroyed
		_moduleLogger.error("%r - %r" % (err, debug))
		self._errorBanner.push_message(err)

	@misc_utils.log_exception(_moduleLogger)
	def _on_continual_update(self, *args):
		if self._isDestroyed:
			return False
		newTime = datetime.datetime.now(tz=time_utils.Mountain)
		oldTime = self._currentTime
		shownTime = self._dateShown

		self._currentTime = newTime
		if shownTime.date() == oldTime.date():
			_moduleLogger.info("Today selected, updating selection")
			self._update_time(newTime)
		return True

	@misc_utils.log_exception(_moduleLogger)
	def _on_player_state_change(self, player, newState):
		if self._presenterNavigation.is_active():
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
			self._update_time(self._dateShown + datetime.timedelta(days=1))
		elif navState == "right":
			self._update_time(self._dateShown - datetime.timedelta(days=1))

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

		currentDate = self._currentTime
		if currentDate.date() != self._dateShown.date():
			self._treeView.get_selection().set_mode(gtk.SELECTION_NONE)
		else:
			self._treeView.get_selection().set_mode(gtk.SELECTION_SINGLE)
			self._select_row()
			go_utils.Async(self._on_delay_scroll).start()

	@misc_utils.log_exception(_moduleLogger)
	def _on_delay_scroll(self, *args):
		self._scroll_to_row()

	@misc_utils.log_exception(_moduleLogger)
	def _on_load_error(self, exception):
		self._hide_loading()
		self._errorBanner.push_message(str(exception))

	@misc_utils.log_exception(_moduleLogger)
	def _on_row_changed(self, selection):
		if len(self._programmingModel) == 0:
			return

		# Undo the user's changing of the selection
		self._select_row()

	def _select_row(self):
		rowIndex = self._get_current_row()
		if rowIndex < 0:
			return
		path = (rowIndex, )
		if not self._treeView.get_selection().path_is_selected(path):
			self._treeView.get_selection().select_path(path)

	def _scroll_to_row(self):
		if self._isDestroyed:
			return
		rowIndex = self._get_current_row()
		if rowIndex < 0:
			return

		path = (rowIndex, )
		self._treeView.scroll_to_cell(path)

		treeViewHeight = self._treeView.get_allocation().height
		viewportHeight = self._viewport.get_allocation().height

		viewsPerPort = treeViewHeight / float(viewportHeight)
		maxRows = len(self._programmingModel)
		percentThrough = rowIndex / float(maxRows)
		dxByIndex = int(viewsPerPort * percentThrough * viewportHeight)

		dxMax = max(treeViewHeight - viewportHeight, 0)

		dx = min(dxByIndex, dxMax)
		adjustment = self._treeScroller.get_vadjustment()
		adjustment.value = dx


gobject.type_register(RadioWindow)
