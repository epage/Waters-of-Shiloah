import os

import cairo
import gtk


class ImageStore(object):

	STORE_LOOKUP = {
		"next": "next.png",
		"prev": "prev.png",
		"pause": "pause.png",
		"play": "play.png",
		"stop": "stop.png",
		"generic_background": "radiobackground_01.png",
		"night_temple_background": "radiobackground_02.png",
		"day_temple_background": "radiobackground_03.png",
		"presidency_background": "radiobackground_04.png",
		"scriptures_background": "radiobackground_05.png",
		"conference": "conference.png",
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

	def get_surface_from_store(self, image):
		path = os.path.join(self._storePath, image)
		image = cairo.ImageSurface.create_from_png(path)
		return image

	def get_image_from_store(self, image):
		path = os.path.join(self._storePath, image)
		image = gtk.Image()
		image.set_from_file(path)
		return image
