import logging

import gobject
import gtk

import hildonize
import util.go_utils as go_utils
import util.misc as misc_utils

import windows


_moduleLogger = logging.getLogger(__name__)


class MagazinesWindow(windows._base.ListWindow):

	def __init__(self, app, player, store, node):
		windows._base.ListWindow.__init__(self, app, player, store, node)
		self._window.set_title(self._node.title)

	@classmethod
	def _get_columns(cls):
		yield gobject.TYPE_PYOBJECT, None

		pixrenderer = gtk.CellRendererPixbuf()
		column = gtk.TreeViewColumn("Covers")
		column.set_property("sizing", gtk.TREE_VIEW_COLUMN_FIXED)
		column.set_property("fixed-width", 96)
		column.pack_start(pixrenderer, expand=True)
		column.add_attribute(pixrenderer, "pixbuf", 1)
		yield gobject.TYPE_OBJECT, column

		textrenderer = gtk.CellRendererText()
		hildonize.set_cell_thumb_selectable(textrenderer)
		column = gtk.TreeViewColumn("Magazine")
		column.set_property("sizing", gtk.TREE_VIEW_COLUMN_FIXED)
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
		for i, programNode in enumerate(programs):
			program = programNode.get_properties()
			img = self._store.get_pixbuf_from_store(self._store.STORE_LOOKUP["nomagazineimage"])
			row = programNode, img, program["title"]
			self._model.append(row)

			programNode.get_children(self._create_on_issues(i), self._on_error)

		self._select_row()
		go_utils.Async(self._on_delay_scroll).start()

	def _create_on_issues(self, row):
		return lambda issues: self._on_issues(row, issues)

	@misc_utils.log_exception(_moduleLogger)
	def _on_issues(self, row, issues):
		for issue in issues:
			self._store.get_pixbuf_from_url(
				issue.get_properties()["pictureURL"],
				lambda pix: self._on_image(row, pix),
				self._on_error,
			)
			break
		else:
			_moduleLogger.info("No issues for magazine %s" % row)

	@misc_utils.log_exception(_moduleLogger)
	def _on_image(self, row, pix):
		treeiter = self._model.iter_nth_child(None, row)
		self._model.set_value(treeiter, 1, pix)
		treeiter = self._model.iter_nth_child(None, row)
		self._model.row_changed((row, ), treeiter)

	@misc_utils.log_exception(_moduleLogger)
	def _on_error(self, exception):
		self._hide_loading()
		self._errorBanner.push_message(str(exception))

	def _window_from_node(self, node):
		issuesWindow = MagazineIssuesWindow(self._app, self._player, self._store, node)
		self._configure_child(issuesWindow)
		issuesWindow.show()
		return issuesWindow


gobject.type_register(MagazinesWindow)


class MagazineIssuesWindow(windows._base.ListWindow):

	def __init__(self, app, player, store, node):
		windows._base.ListWindow.__init__(self, app, player, store, node)
		self._window.set_title(self._node.title)

	@classmethod
	def _get_columns(cls):
		yield gobject.TYPE_PYOBJECT, None

		pixrenderer = gtk.CellRendererPixbuf()
		column = gtk.TreeViewColumn("Covers")
		column.set_property("sizing", gtk.TREE_VIEW_COLUMN_FIXED)
		column.set_property("fixed-width", 96)
		column.pack_start(pixrenderer, expand=True)
		column.add_attribute(pixrenderer, "pixbuf", 1)
		yield gobject.TYPE_OBJECT, column

		textrenderer = gtk.CellRendererText()
		hildonize.set_cell_thumb_selectable(textrenderer)
		column = gtk.TreeViewColumn("Issue")
		column.set_property("sizing", gtk.TREE_VIEW_COLUMN_FIXED)
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

			self._store.get_pixbuf_from_url(
				program["pictureURL"],
				self._create_on_image(programNode),
				self._on_error,
			)

		self._select_row()
		go_utils.Async(self._on_delay_scroll).start()

	@misc_utils.log_exception(_moduleLogger)
	def _on_error(self, exception):
		self._hide_loading()
		self._errorBanner.push_message(str(exception))

	def _create_on_image(self, programNode):
		return lambda pix: self._on_image(programNode, pix)

	@misc_utils.log_exception(_moduleLogger)
	def _on_image(self, childNode, pix):
		for i, row in enumerate(self._model):
			if row[0] is childNode:
				break
		else:
			raise RuntimeError("Could not find %r" % childNode)
		treeiter = self._model.iter_nth_child(None, i)
		self._model.set_value(treeiter, 1, pix)
		treeiter = self._model.iter_nth_child(None, i)
		self._model.row_changed((i, ), treeiter)

	def _window_from_node(self, node):
		issuesWindow = MagazineArticlesWindow(self._app, self._player, self._store, node)
		self._configure_child(issuesWindow)
		issuesWindow.show()
		return issuesWindow


gobject.type_register(MagazineIssuesWindow)


class MagazineArticlesWindow(windows._base.ListWindow):

	def __init__(self, app, player, store, node):
		windows._base.ListWindow.__init__(self, app, player, store, node)
		self._window.set_title(self._node.title)

	@classmethod
	def _get_columns(cls):
		yield gobject.TYPE_PYOBJECT, None

		textrenderer = gtk.CellRendererText()
		column = gtk.TreeViewColumn("Article")
		column.set_property("sizing", gtk.TREE_VIEW_COLUMN_FIXED)
		column.pack_start(textrenderer, expand=True)
		column.add_attribute(textrenderer, "markup", 1)
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
			row = programNode, "%s\n<small>%s</small>" % (programNode.title, programNode.subtitle)
			self._model.append(row)

		self._select_row()
		go_utils.Async(self._on_delay_scroll).start()

	@misc_utils.log_exception(_moduleLogger)
	def _on_error(self, exception):
		self._hide_loading()
		self._errorBanner.push_message(str(exception))

	def _window_from_node(self, node):
		issuesWindow = MagazineArticleWindow(self._app, self._player, self._store, node)
		self._configure_child(issuesWindow)
		issuesWindow.show()
		return issuesWindow


gobject.type_register(MagazineArticlesWindow)


class MagazineArticleWindow(windows._base.PresenterWindow):

	def __init__(self, app, player, store, node):
		windows._base.PresenterWindow.__init__(self, app, player, store, node)

	def _get_background(self, orientation):
		if orientation == gtk.ORIENTATION_VERTICAL:
			return self._store.STORE_LOOKUP["magazine_background"]
		elif orientation == gtk.ORIENTATION_HORIZONTAL:
			return self._store.STORE_LOOKUP["magazine_background_landscape"]
		else:
			raise NotImplementedError("Unknown orientation %s" % orientation)


gobject.type_register(MagazineArticleWindow)
