#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
@bug For some reason, the back/close button doesn't work when I nest multiple levels
@bug When switching from conference to magazines, it randomly jumps around and duplicates windows

@todo Re-use windows for better performance
@todo Make radio program updates only happen when the app has focus to reduce CPU wakes
@todo Need to confirm id's are persistent (not just for todos but broken behavior on transition)
	@todo Track recent
	@todo Persisted Pause
	@todo Favorites
@todo Sleep timer
@todo Reverse order option.  Toggle between playing ascending/descending chronological order
@todo Podcast integration
	@todo Default with BYU Devotionals, http://speeches.byu.edu/?act=help&page=podcast
"""

from __future__ import with_statement

import os
import gc
import logging
import ConfigParser

import gobject
import dbus
import dbus.mainloop.glib
import gtk

try:
	import osso
except ImportError:
	osso = None

import constants
import hildonize
import util.misc as misc_utils

import imagestore
import player
import stream_index
import windows


_moduleLogger = logging.getLogger(__name__)
PROFILE_STARTUP = False


class MormonChannelProgram(hildonize.get_app_class()):

	def __init__(self):
		super(MormonChannelProgram, self).__init__()
		currentPath = os.path.abspath(__file__)
		storePath = os.path.join(os.path.split(os.path.dirname(currentPath))[0], "data")
		self._store = imagestore.ImageStore(storePath, constants._cache_path_)
		self._index = stream_index.AudioIndex()
		self._player = player.Player(self._index)

		self._store.start()
		self._index.start()
		try:
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

			self._sourceSelector = windows.source.SourceSelector(self, self._player, self._store, self._index)
			self._sourceSelector.window.connect("destroy", self._on_destroy)
			self._sourceSelector.window.set_default_size(400, 800)
			self._sourceSelector.show()
			self._load_settings()
		except:
			self._index.stop()
			self._store.stop()
			raise

	def _save_settings(self):
		config = ConfigParser.SafeConfigParser()

		self._sourceSelector.save_settings(config, "Windows")

		with open(constants._user_settings_, "wb") as configFile:
			config.write(configFile)

	def _load_settings(self):
		config = ConfigParser.SafeConfigParser()
		config.read(constants._user_settings_)

		self._sourceSelector.load_settings(config, "Windows")

	@misc_utils.log_exception(_moduleLogger)
	def _on_device_state_change(self, shutdown, save_unsaved_data, memory_low, system_inactivity, message, userData):
		"""
		For system_inactivity, we have no background tasks to pause

		@note Hildon specific
		"""
		if memory_low:
			gc.collect()

		if save_unsaved_data or shutdown:
			self._save_settings()

	@misc_utils.log_exception(_moduleLogger)
	def _on_destroy(self, widget = None, data = None):
		try:
			self.quit()
		finally:
			gtk.main_quit()

	def quit(self):
		self._save_settings()

		self._player.stop()
		self._index.stop()
		self._store.stop()

		try:
			self._deviceState.close()
		except AttributeError:
			pass # Either None or close was removed (in Fremantle)
		try:
			self._osso_c.close()
		except AttributeError:
			pass # Either None or close was removed (in Fremantle)

	@misc_utils.log_exception(_moduleLogger)
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
	gobject.threads_init()
	gtk.gdk.threads_init()
	l = dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)

	hildonize.set_application_name("FMRadio") # Playback while silent on Maemo 5
	app = MormonChannelProgram()
	if not PROFILE_STARTUP:
		try:
			gtk.main()
		except KeyboardInterrupt:
			app.quit()
			raise
	else:
		app.quit()


if __name__ == "__main__":
	logging.basicConfig(level=logging.DEBUG)
	run()
