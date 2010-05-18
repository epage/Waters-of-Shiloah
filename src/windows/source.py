import logging

import gobject
import gtk

import constants
import util.misc as misc_utils
import banners
import playcontrol
import stream_index

import windows


_moduleLogger = logging.getLogger(__name__)


class SourceSelector(windows._base.BasicWindow):

	def __init__(self, app, player, store, index):
		windows._base.BasicWindow.__init__(self, app, player, store)
		self._languages = []
		self._index = index

		self._loadingBanner = banners.GenericBanner()

		self._radioButton = self._create_button("radio", "Radio")
		self._radioButton.connect("clicked", self._on_source_selected, stream_index.SOURCE_RADIO)

		self._conferenceButton = self._create_button("conferences", "Conferences")
		self._conferenceButton.connect("clicked", self._on_source_selected, stream_index.SOURCE_CONFERENCES)

		self._magazineButton = self._create_button("magazines", "Magazines")
		self._magazineButton.connect("clicked", self._on_source_selected, stream_index.SOURCE_MAGAZINES)

		self._scriptureButton = self._create_button("scriptures", "Scriptures")
		self._scriptureButton.connect("clicked", self._on_source_selected, stream_index.SOURCE_SCRIPTURES)

		self._buttonLayout = gtk.VButtonBox()
		self._buttonLayout.set_layout(gtk.BUTTONBOX_SPREAD)
		self._buttonLayout.pack_start(self._radioButton, True, True)
		self._buttonLayout.pack_start(self._conferenceButton, True, True)
		self._buttonLayout.pack_start(self._magazineButton, True, True)
		self._buttonLayout.pack_start(self._scriptureButton, True, True)

		self._separator = gtk.HSeparator()
		self._playcontrol = playcontrol.NavControl(player, store)
		self._playcontrol.connect("jump-to", self._on_jump)

		self._layout.pack_start(self._loadingBanner.toplevel, False, False)
		self._layout.pack_start(self._buttonLayout, True, True)
		self._layout.pack_start(self._separator, False, True)
		self._layout.pack_start(self._playcontrol.toplevel, False, True)

		self._window.set_title(constants.__pretty_app_name__)

	def show(self):
		windows._base.BasicWindow.show(self)

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
		label.set_use_markup(True)
		label.set_markup("<big>%s</big>" % message)

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

	def _window_from_node(self, node):
		if node.id == stream_index.SOURCE_RADIO:
			Source = windows.radio.RadioWindow
		elif node.id == stream_index.SOURCE_CONFERENCES:
			Source = windows.conferences.ConferencesWindow
		elif node.id == stream_index.SOURCE_MAGAZINES:
			Source = windows.magazines.MagazinesWindow
		elif node.id == stream_index.SOURCE_SCRIPTURES:
			Source = windows.scriptures.ScripturesWindow
		sourceWindow = Source(self._app, self._player, self._store, node)
		sourceWindow.window.set_modal(True)
		sourceWindow.window.set_transient_for(self._window)
		sourceWindow.window.set_default_size(*self._window.get_size())
		sourceWindow.connect("quit", self._on_quit)
		sourceWindow.connect("jump-to", self._on_jump)
		sourceWindow.show()
		return sourceWindow

	@misc_utils.log_exception(_moduleLogger)
	def _on_jump(self, source, node):
		targetNodePath = list(reversed(list(stream_index.walk_ancestors(node))))
		ancestor = targetNodePath[0]
		window = self._window_from_node(ancestor)
		window.jump_to(node)

	@misc_utils.log_exception(_moduleLogger)
	def _on_source_selected(self, widget, nodeName):
		node = self._index.get_source(nodeName, self._languages[0]["id"])
		self._window_from_node(node)


gobject.type_register(SourceSelector)

