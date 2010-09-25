from __future__ import with_statement

import os
import logging

import cairo
import gtk

import browser_emu
from util import go_utils
import util.misc as misc_utils


_moduleLogger = logging.getLogger(__name__)


class ImageStore(object):

	STORE_LOOKUP = {
		"next": "button_next.png",
		"prev": "button_prev.png",
		"home": "icon.png",
		"pause": "button_pause.png",
		"play": "button_play.png",
		"stop": "button_stop.png",
		"add": "button_add.png",
		"remove": "button_remove.png",
		"favorite": "button_favorite.png",
		"next_pressed": "button_next_pressed.png",
		"prev_pressed": "button_prev_pressed.png",
		"home_pressed": "icon.png",
		"pause_pressed": "button_pause_pressed.png",
		"play_pressed": "button_play_pressed.png",
		"stop_pressed": "button_stop_pressed.png",
		"add_pressed": "button_add_pressed.png",
		"remove_pressed": "button_remove_pressed.png",
		"favorite_pressed": "button_favorite_pressed.png",

		"radio_header": "radio_header.png",
		"conference_background": "background_conference_p.png",
		"conference_background_landscape": "background_conference_l.png",
		"magazine_background": "background_magazines_p.png",
		"magazine_background_landscape": "background_magazines_l.png",
		"scripture_background": "background_scriptures_p.png",
		"scripture_background_landscape": "background_scriptures_l.png",

		"conferences": "label_conference.png",
		"magazines": "label_magazines.png",
		"radio": "label_radio.png",
		"scriptures": "label_scriptures.png",

		"loading": "loading.gif",
		"icon": "icon.png",
		"nomagazineimage": "nomagazineimage.png",
	}

	def __init__(self, storePath, cachePath):
		self._storePath = storePath
		self._cachePath = cachePath

		self._browser = browser_emu.MozillaEmulator()
		self._downloader = go_utils.AsyncPool()

	def start(self):
		self._downloader.start()

	def stop(self):
		self._downloader.stop()

	def get_surface_from_store(self, imageName):
		path = os.path.join(self._storePath, imageName)
		image = cairo.ImageSurface.create_from_png(path)
		return image

	def get_image_from_store(self, imageName):
		path = os.path.join(self._storePath, imageName)
		image = gtk.Image()
		image.set_from_file(path)
		return image

	def set_image_from_store(self, image, imageName):
		path = os.path.join(self._storePath, imageName)
		image.set_from_file(path)
		return image

	def get_pixbuf_from_store(self, imageName):
		path = os.path.join(self._storePath, imageName)
		return gtk.gdk.pixbuf_new_from_file(path)

	def get_pixbuf_from_url(self, url, on_success, on_error):
		# @ todo Test bad image for both paths
		filepath = self._url_to_cache(url)
		if os.path.exists(filepath):
			pix = gtk.gdk.pixbuf_new_from_file(filepath)
			try:
				on_success(pix)
			except Exception:
				pass
			doDownload = False
		else:
			doDownload = True

		if doDownload:
			self._get_image(
				url,
				lambda filepath: on_success(gtk.gdk.pixbuf_new_from_file(filepath)),
				on_error,
			)

	def get_pixbuf_animation_from_store(self, imageName):
		path = os.path.join(self._storePath, imageName)
		return gtk.gdk.PixbufAnimation(path)

	def _get_image(self, url, on_success, on_error):
		self._downloader.add_task(
			self._browser.download,
			(url, ),
			{},
			lambda image: self._on_get_image(url, image, on_success, on_error),
			on_error,
		)

	@misc_utils.log_exception(_moduleLogger)
	def _on_get_image(self, url, image, on_success, on_error):
		try:
			filepath = self._url_to_cache(url)
			_moduleLogger.info("Saved %s" % filepath)
			with open(filepath, "wb") as f:
				f.write(image)
			on_success(filepath)
		except Exception, e:
			on_error(e)

	def _url_to_cache(self, url):
		filename = url.rsplit("/", 1)[-1]
		filepath = os.path.join(self._cachePath, filename)
		return filepath
