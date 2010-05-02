#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import with_statement

import gc
import logging
import ConfigParser

import gtk

try:
	import hildon
except ImportError:
	hildon = None

try:
	import osso
except ImportError:
	osso = None

import constants
import hildonize
import gtk_toolbox

import imagestore
import player
import windows


_moduleLogger = logging.getLogger(__name__)
PROFILE_STARTUP = False


class MormonChannelProgram(hildonize.get_app_class()):

	def __init__(self):
		super(MormonChannelProgram, self).__init__()
		self._clipboard = gtk.clipboard_get()

		self._window_in_fullscreen = False #The window isn't in full screen mode initially.

		#Create GUI main vbox
		vbox = gtk.VBox(homogeneous = False, spacing = 0)

		if hildonize.GTK_MENU_USED:
			#Create Menu and apply it for hildon
			filemenu = gtk.Menu()

			menu_items = gtk.MenuItem("Quit")
			filemenu.append(menu_items)
			menu_items.connect("activate", self._on_destroy, None)

			file_menu = gtk.MenuItem("File")
			file_menu.show()
			file_menu.set_submenu(filemenu)

			categorymenu = gtk.Menu()

			menu_items = gtk.MenuItem("Search")
			categorymenu.append(menu_items)
			menu_items.connect("activate", self._on_toggle_search)

			helpmenu = gtk.Menu()

			menu_items = gtk.MenuItem("About")
			helpmenu.append(menu_items)
			menu_items.connect("activate", self._on_show_about, None)

			help_menu = gtk.MenuItem("Help")
			help_menu.show()
			help_menu.set_submenu(helpmenu)

			menuBar = gtk.MenuBar()
			menuBar.show()
			menuBar.append (file_menu)
			menuBar.append (help_menu)

			vbox.pack_start(menuBar, False, False, 0)
		else:
			menuBar = gtk.MenuBar()
			menuBar.show()
			vbox.pack_start(menuBar, False, False, 0)

		#Get the Main Window, and connect the "destroy" event
		self._window = gtk.Window()
		self._window.add(vbox)

		self._window = hildonize.hildonize_window(self, self._window)
		hildonize.set_application_title(self._window, "%s" % constants.__pretty_app_name__)
		menuBar = hildonize.hildonize_menu(
			self._window,
			menuBar,
		)
		if hildonize.IS_FREMANTLE_SUPPORTED:
			searchButton= gtk.Button("Search")
			searchButton.connect("clicked", self._on_toggle_search)
			menuBar.append(searchButton)

			menuBar.show_all()

		if not hildonize.IS_HILDON_SUPPORTED:
			_moduleLogger.info("No hildonization support")

		if osso is not None:
			self._osso_c = osso.Context(constants.__app_name__, constants.__version__, False)
			self._deviceState = osso.DeviceState(self._osso_c)
			self._deviceState.set_device_state_callback(self._on_device_state_change, 0)
		else:
			_moduleLogger.info("No osso support")
			self._osso_c = None
			self._deviceState = None

		self._window.connect("delete-event", self._on_delete_event)
		self._window.connect("destroy", self._on_destroy)
		self._window.connect("key-press-event", self._on_key_press)
		self._window.connect("window-state-event", self._on_window_state_change)

		self._window.show_all()

		self._player = player.Player()
		self._store = imagestore.ImageStore("../data", "../data")
		self._windowStack = [windows.SourceSelector(self._player, self._store)]
		vbox.pack_start(self._windowStack[0].toplevel, True, True)

		self._load_settings()

	def _save_settings(self):
		config = ConfigParser.SafeConfigParser()
		self.save_settings(config)
		with open(constants._user_settings_, "wb") as configFile:
			config.write(configFile)

	def save_settings(self, config):
		config.add_section(constants.__pretty_app_name__)
		config.set(constants.__pretty_app_name__, "fullscreen", str(self._window_in_fullscreen))

	def _load_settings(self):
		config = ConfigParser.SafeConfigParser()
		config.read(constants._user_settings_)
		self.load_settings(config)

	def load_settings(self, config):
		try:
			self._window_in_fullscreen = config.getboolean(constants.__pretty_app_name__, "fullscreen")
		except ConfigParser.NoSectionError, e:
			_moduleLogger.info(
				"Settings file %s is missing section %s" % (
					constants._user_settings_,
					e.section,
				)
			)

		if self._window_in_fullscreen:
			self._window.fullscreen()
		else:
			self._window.unfullscreen()

	def _toggle_search(self):
		if self._search.get_property("visible"):
			self._search.hide()
		else:
			self._search.show()

	@gtk_toolbox.log_exception(_moduleLogger)
	def _on_device_state_change(self, shutdown, save_unsaved_data, memory_low, system_inactivity, message, userData):
		"""
		For system_inactivity, we have no background tasks to pause

		@note Hildon specific
		"""
		if memory_low:
			gc.collect()

		if save_unsaved_data or shutdown:
			self._save_settings()

	@gtk_toolbox.log_exception(_moduleLogger)
	def _on_window_state_change(self, widget, event, *args):
		if event.new_window_state & gtk.gdk.WINDOW_STATE_FULLSCREEN:
			self._window_in_fullscreen = True
		else:
			self._window_in_fullscreen = False

	@gtk_toolbox.log_exception(_moduleLogger)
	def _on_key_press(self, widget, event, *args):
		RETURN_TYPES = (gtk.keysyms.Return, gtk.keysyms.ISO_Enter, gtk.keysyms.KP_Enter)
		isCtrl = bool(event.get_state() & gtk.gdk.CONTROL_MASK)
		if (
			event.keyval == gtk.keysyms.F6 or
			event.keyval in RETURN_TYPES and isCtrl
		):
			# The "Full screen" hardware key has been pressed 
			if self._window_in_fullscreen:
				self._window.unfullscreen ()
			else:
				self._window.fullscreen ()
			return True
		elif event.keyval == gtk.keysyms.f and isCtrl:
			self._toggle_search()
			return True
		elif (
			event.keyval in (gtk.keysyms.w, gtk.keysyms.q) and
			event.get_state() & gtk.gdk.CONTROL_MASK
		):
			self._window.destroy()
		elif event.keyval == gtk.keysyms.l and event.get_state() & gtk.gdk.CONTROL_MASK:
			with open(constants._user_logpath_, "r") as f:
				logLines = f.xreadlines()
				log = "".join(logLines)
				self._clipboard.set_text(str(log))
			return True

	@gtk_toolbox.log_exception(_moduleLogger)
	def _on_toggle_search(self, *args):
		self._toggle_search()

	@gtk_toolbox.log_exception(_moduleLogger)
	def _on_delete_event(self, widget, event, data = None):
		return False

	@gtk_toolbox.log_exception(_moduleLogger)
	def _on_destroy(self, widget = None, data = None):
		try:
			self._save_settings()

			try:
				self._deviceState.close()
			except AttributeError:
				pass # Either None or close was removed (in Fremantle)
			try:
				self._osso_c.close()
			except AttributeError:
				pass # Either None or close was removed (in Fremantle)
		finally:
			gtk.main_quit()

	@gtk_toolbox.log_exception(_moduleLogger)
	def _on_show_about(self, widget = None, data = None):
		dialog = gtk.AboutDialog()
		dialog.set_position(gtk.WIN_POS_CENTER)
		dialog.set_name(constants.__pretty_app_name__)
		dialog.set_version(constants.__version__)
		dialog.set_copyright("")
		dialog.set_website("")
		comments = "Mormon Radio and Audiobook Player"
		dialog.set_comments(comments)
		dialog.set_authors(["Ed Page <eopage@byu.net>"])
		dialog.run()
		dialog.destroy()


def run():
	if hildonize.IS_HILDON_SUPPORTED:
		gtk.set_application_name(constants.__pretty_app_name__)
	app = MormonChannelProgram()
	if not PROFILE_STARTUP:
		gtk.main()


if __name__ == "__main__":
	logging.basicConfig(level=logging.DEBUG)
	run()
