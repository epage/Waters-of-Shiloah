import gtk

import banners
import playcontrol


class SourceSelector(object):

	def __init__(self, player, store):
		self._player = player
		self._store = store

		self._errorBanner = banners.StackingBanner()

		self._radioButton = self._create_button("radio", "Radio")
		self._radioWrapper = gtk.VBox()
		self._radioWrapper.pack_start(self._radioButton, False, True)
		self._conferenceButton = self._create_button("conferences", "Conferences")
		self._conferenceWrapper = gtk.VBox()
		self._conferenceWrapper.pack_start(self._conferenceButton, False, True)
		self._magazineButton = self._create_button("magazines", "Magazines")
		self._magazineWrapper = gtk.VBox()
		self._magazineWrapper.pack_start(self._magazineButton, False, True)
		self._scriptureButton = self._create_button("scriptures", "Scriptures")
		self._scriptureWrapper = gtk.VBox()
		self._scriptureWrapper.pack_start(self._scriptureButton, False, True)

		self._buttonLayout = gtk.VBox(True, 5)
		self._buttonLayout.set_property("border-width", 5)
		self._buttonLayout.pack_start(self._radioWrapper, True, True)
		self._buttonLayout.pack_start(self._conferenceWrapper, True, True)
		self._buttonLayout.pack_start(self._magazineWrapper, True, True)
		self._buttonLayout.pack_start(self._scriptureWrapper, True, True)

		self._playcontrol = playcontrol.PlayControl(player, store)

		self._layout = gtk.VBox()
		self._layout.pack_start(self._errorBanner.toplevel, False, True)
		self._layout.pack_start(self._buttonLayout, True, True)
		self._layout.pack_start(self._playcontrol.toplevel, False, True)

		self._layout.show_all()
		self._errorBanner.toplevel.hide()
		self._playcontrol.toplevel.hide()

	@property
	def toplevel(self):
		return self._layout

	def _create_button(self, icon, message):
		image = self._store.get_image_from_store(self._store.STORE_LOOKUP[icon])

		label = gtk.Label()
		label.set_text(message)

		buttonLayout = gtk.HBox(False, 5)
		buttonLayout.pack_start(image, False, False)
		buttonLayout.pack_start(label, False, True)
		button = gtk.Button()
		button.add(buttonLayout)

		return button
