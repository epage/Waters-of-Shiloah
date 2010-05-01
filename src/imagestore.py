import os

import cairo
import gtk


class ImageStore(object):

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
