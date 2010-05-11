#!/usr/bin/env python

import sys
import logging

import gtk

sys.path.append('../src')

import imagestore
import playcontrol
import fake_player


if __name__ == "__main__":
	logging.basicConfig(level=logging.DEBUG)

	store = imagestore.ImageStore("../data", ".")

	player = fake_player.FakePlayer()
	sp = playcontrol.PlayControl(player, store)

	layout = gtk.VBox()
	layout.pack_start(player.toplevel)
	layout.pack_start(sp.toplevel)

	window = gtk.Window()
	window.set_title("Test")
	window.add(layout)
	window.connect("destroy", lambda w: gtk.main_quit())
	window.show_all()

	sp.refresh()

	gtk.main()
