#!/usr/bin/env python

import urllib
from xml.etree import ElementTree
import logging

import browser_emu


_moduleLogger = logging.getLogger(__name__)


class Backend(object):

	def __init__(self):
		self._browser = browser_emu.MozillaEmulator()

	def get_languages(self):
		tree = self._get_page_with_validation(
			action="lds.radio.languages.query",
		)
		languages = tree.find("languages")
		return self._process_list(languages, ["name"])

	def get_radio_channels(self):
		tree = self._get_page_with_validation(
			action="lds.radio.radiochannels.query",
		)
		channels = tree.find("channels")
		return self._process_list(channels, ["description", "url", "port"])

	def get_radio_channel_programming(self, chanId, date=None):
		if date is not None:
			date = date.strftime("%Y-%m-%d")
			tree = self._get_page_with_validation(
				action="lds.radio.radiochannels.programming.query",
				channelID=chanId,
				date=date,
			)
		else:
			tree = self._get_page_with_validation(
				action="lds.radio.radiochannels.programming.query",
				channelID=chanId,
			)
		programs = tree.find("programs")
		return self._process_list(programs, ["date", "time", "title", "shortdescription", "artist"])

	def get_conferences(self, langId):
		tree = self._get_page_with_validation(
			action="lds.radio.conferences.query",
			languageID=langId,
		)
		conferences = tree.find("conferences")
		return self._process_list(conferences, ["title", "full_title", "month", "year"])

	def get_conference_sessions(self, confId):
		tree = self._get_page_with_validation(
			action="lds.radio.conferences.sessions.query",
			conferenceID=confId,
		)
		items = tree.find("sessions")
		return self._process_list(items, ["title", "short_title", "order"])

	def get_conference_talks(self, sessionId):
		tree = self._get_page_with_validation(
			action="lds.radio.conferences.sessions.talks.query",
			sessionID=sessionId,
		)
		items = tree.find("talks")
		return self._process_list(items, ["title", "order", "url", "speaker"])

	def get_magazines(self, langId):
		tree = self._get_page_with_validation(
			action="lds.radio.magazines.query",
			languageID=langId,
		)
		magazines = tree.find("magazines")
		return self._process_list(magazines, ["title"])

	def get_magazine_issues(self, magId):
		tree = self._get_page_with_validation(
			action="lds.radio.magazines.issues.query",
			magazineID=magId,
		)
		items = tree.find("issues")
		return self._process_list(items, ["title", "year", "month", "pictureURL"])

	def get_magazine_articles(self, issueId):
		tree = self._get_page_with_validation(
			action="lds.radio.magazines.issues.articles.query",
			issueID=issueId,
		)
		items = tree.find("articles")
		return self._process_list(items, ["title", "author", "url"])

	def get_scriptures(self, langId):
		tree = self._get_page_with_validation(
			action="lds.radio.scriptures.query",
			languageID=langId,
		)
		scriptures = tree.find("scriptures")
		return self._process_list(scriptures, ["title"])

	def get_scripture_books(self, scriptId):
		tree = self._get_page_with_validation(
			action="lds.radio.scriptures.books.query",
			scriptureID=scriptId,
		)
		items = tree.find("books")
		return self._process_list(items, ["title"])

	def get_scripture_chapters(self, bookId):
		tree = self._get_page_with_validation(
			action="lds.radio.scriptures.books.chapters.query",
			bookID=bookId,
		)
		items = tree.find("chapters")
		return self._process_list(items, ["title", "url"])

	def _get_page_with_validation(self, **params):
		encodedParams = urllib.urlencode(params)
		page = self._browser.download("http://tech.lds.org/radio?%s" % encodedParams)
		if not page:
			raise RuntimeError("Blank page")
		tree = ElementTree.fromstring(page)

		if tree.tag == "apiresults":
			desc = tree.find("ErrorDescription")
			raise RuntimeError(desc.text)
		else:
			results = tree.find("apiresults")
			if not results.attrib["success"]:
				raise RuntimeError("Could not determine radio languages")

		return tree

	def _process_list(self, tree, elements):
		for item in tree.getchildren():
			data = {"id": item.attrib["ID"]}
			for element in elements:
				data[element] = item.find(element).text
			yield data


if __name__ == "__main__":
	b = Backend()

	print list(b.get_languages())

	if False:
		channels = list(b.get_radio_channels())
		print channels
		for chanData in channels:
			programs = list(b.get_radio_channel_programming(chanData["id"]))
			print programs

	if False:
		confs = list(b.get_conferences(1))
		print confs
		for confData in confs:
			sessions = list(b.get_conference_sessions(confData["id"]))
			for sessionData in sessions:
				talks = list(b.get_conference_talks(sessionData["id"]))
				print talks

	if False:
		mags = list(b.get_magazines(1))
		print mags
		for magData in mags:
			issues = list(b.get_magazine_issues(magData["id"]))
			issues
			for issueData in issues:
				articles = list(b.get_magazine_articles(issueData["id"]))
				print articles

	if False:
		mags = list(b.get_scriptures(1))
		print mags
		for magData in mags:
			books = list(b.get_scripture_books(magData["id"]))
			print books
			for bookData in books:
				chapters = list(b.get_scripture_chapters(bookData["id"]))
				print chapters
