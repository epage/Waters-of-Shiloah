#!/usr/bin/python2.5

import os
import sys

try:
	import py2deb
except ImportError:
	import fake_py2deb as py2deb

import constants


__appname__ = constants.__app_name__
__description__ = """Media player for inspirational streaming radio and audiobooks including the KJV Bible
Supports streaming:
* "Mormon Channel" inspirational radio station
* Conference precedings and magazines from The Church of Jesus Christ of Latter-day Saints
* Scriptures, including King James Version of the Bible and the Book of Mormon
.
This application is not endorsed by The Church of Jesus Christ of Latter-day Saints
.
Homepage: http://watersofshiloah.garage.maemo.org
"""
__author__ = "Ed Page"
__email__ = "eopage@byu.net"
__version__ = constants.__version__
__build__ = constants.__build__
__changelog__ = """
* Fixing Maemo 4.1
"""


__postinstall__ = """#!/bin/sh -e

gtk-update-icon-cache -f /usr/share/icons/hicolor
rm -f ~/.%(name)s/%(name)s.log
""" % {"name": constants.__app_name__}

__preremove__ = """#!/bin/sh -e
"""


def find_files(prefix, path):
	for root, dirs, files in os.walk(path):
		for file in files:
			if file.startswith(prefix+"-"):
				fileParts = file.split("-")
				unused, relPathParts, newName = fileParts[0], fileParts[1:-1], fileParts[-1]
				assert unused == prefix
				relPath = os.sep.join(relPathParts)
				yield relPath, file, newName


def unflatten_files(files):
	d = {}
	for relPath, oldName, newName in files:
		if relPath not in d:
			d[relPath] = []
		d[relPath].append((oldName, newName))
	return d


def build_package(distribution):
	try:
		os.chdir(os.path.dirname(sys.argv[0]))
	except:
		pass

	py2deb.Py2deb.SECTIONS = py2deb.SECTIONS_BY_POLICY[distribution]
	p = py2deb.Py2deb(__appname__)
	p.prettyName = constants.__pretty_app_name__
	p.description = __description__
	p.bugTracker = "https://bugs.maemo.org/enter_bug.cgi?product=Waters%%20of%%20Shiloah"
	p.author = __author__
	p.mail = __email__
	p.license = "lgpl"
	p.depends = ", ".join([
		"python2.6 | python2.5",
		"python-gtk2 | python2.5-gtk2",
		"python-xml | python2.5-xml",
		"python-dbus | python2.5-dbus",
		"python-telepathy | python2.5-telepathy",
	])
	maemoSpecificDepends = ", python-osso | python2.5-osso, python-hildon | python2.5-hildon"
	p.depends += {
		"debian": ", python-gst0.10",
		"diablo": maemoSpecificDepends,
		"fremantle": maemoSpecificDepends + ", python-gst0.10",
	}[distribution]
	p.recommends = ", ".join([
	])
	p.section = {
		"debian": "sound",
		"diablo": "user/multimedia",
		"fremantle": "user/multimedia",
	}[distribution]
	p.arch = "all"
	p.urgency = "low"
	p.distribution = "diablo fremantle debian"
	p.repository = "extras"
	p.changelog = __changelog__
	p.postinstall = __postinstall__
	p.icon = "48x48-WatersOfShiloah.png"
	p["/opt/WatersOfShiloah/bin"] = ["WatersOfShiloah.py"]
	for relPath, files in unflatten_files(find_files("src", ".")).iteritems():
		fullPath = "/opt/WatersOfShiloah/lib"
		if relPath:
			fullPath += os.sep+relPath
		fileLocationTransforms = list(
			"|".join((oldName, newName))
			for (oldName, newName) in files
		)
		if not relPath:
			fileLocationTransforms.append({
				"debian": "src-stream_gst.py|stream.py",
				"diablo": "src-stream_osso.py|stream.py",
				"fremantle": "src-stream_gst.py|stream.py",
			}[distribution])
		p[fullPath] = fileLocationTransforms
	for relPath, files in unflatten_files(find_files("data", ".")).iteritems():
		fullPath = "/opt/WatersOfShiloah/share"
		if relPath:
			fullPath += os.sep+relPath
		p[fullPath] = list(
			"|".join((oldName, newName))
			for (oldName, newName) in files
		)
	p["/usr/share/applications/hildon"] = ["WatersOfShiloah.desktop"]
	p["/usr/share/icons/hicolor/48x48/hildon"] = ["48x48-WatersOfShiloah.png|WatersOfShiloah.png"]

	if distribution == "debian":
		print p
		print p.generate(
			version="%s-%s" % (__version__, __build__),
			changelog=__changelog__,
			build=True,
			tar=False,
			changes=False,
			dsc=False,
		)
		print "Building for %s finished" % distribution
	else:
		print p
		print p.generate(
			version="%s-%s" % (__version__, __build__),
			changelog=__changelog__,
			build=False,
			tar=True,
			changes=True,
			dsc=True,
		)
		print "Building for %s finished" % distribution


if __name__ == "__main__":
	if len(sys.argv) > 1:
		try:
			import optparse
		except ImportError:
			optparse = None

		if optparse is not None:
			parser = optparse.OptionParser()
			(commandOptions, commandArgs) = parser.parse_args()
	else:
		commandArgs = None
		commandArgs = ["diablo"]
	build_package(commandArgs[0])
