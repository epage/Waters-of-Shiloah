import os

import cairo
import gtk


class ImageStore(object):

	STORE_LOOKUP = {
		"next": "next.png",
		"prev": "prev.png",
		"home": "home.png",
		"pause": "pause.png",
		"play": "play.png",
		"stop": "stop.png",
		"pause_pressed": "pausepressed.png",
		"play_pressed": "playpressed.png",
		"stop_pressed": "stoppressed.png",

		"small_next": "small_next.png",
		"small_prev": "small_prev.png",
		"small_home": "small_home.png",
		"small_pause": "small_pause.png",
		"small_play": "small_play.png",
		"small_stop": "small_stop.png",
		"small_pause_pressed": "small_pausepressed.png",
		"small_play_pressed": "small_playpressed.png",
		"small_stop_pressed": "small_stoppressed.png",

		"loading": "loading.gif",

		"radio_header": "radio_header.png",
		"conference_background": "conference_bg.png",
		"magazine_background": "magazine_bg.png",
		"scripture_background": "scripture_bg.png",

		"conferences": "conference.png",
		"magazines": "magazines.png",
		"more": "more.png",
		"mormonmessages": "mormonmessages.png",
		"radio": "radio.png",
		"scriptures": "scriptures.png",
		"icon": "icon.png",
	}

	def __init__(self, storePath, cachePath):
		self._storePath = storePath
		self._cachePath = cachePath

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

	def get_pixbuf_animation_from_store(self, imageName):
		path = os.path.join(self._storePath, imageName)
		return gtk.gdk.PixbufAnimation(path)
