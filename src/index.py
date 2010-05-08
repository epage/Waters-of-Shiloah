import weakref
import logging

import util.misc as misc_utils
from util import go_utils
import backend


_moduleLogger = logging.getLogger(__name__)


class Connection(object):

	def __init__(self):
		self._backend = backend.Backend()
		self._indexing = go_utils.AsyncPool()

	def start(self):
		self._indexing.start()

	def stop(self):
		self._indexing.stop()

	def download(self, func, on_success, on_error, args = None, kwds = None):
		if args is None:
			args = ()
		if kwds is None:
			kwds = {}

		self._indexing.clear_tasks()
		self._indexing.add_task(
			getattr(self._backend, func),
			args,
			kwds,
			on_success,
			on_error,
		)


class AudioIndex(object):

	def __init__(self):
		self._connection = Connection()
		self._languages = None
		self._languagesRequest = None
		self._sources = {}

	def start(self):
		self._connection.start()

	def stop(self):
		self._connection.stop()

	def get_languages(self, on_success, on_error):
		if self._languages is None:
			assert self._languagesRequest is None
			self._languagesRequest = on_success, on_error
			self._connection.download(
				"get_languages",
				self._on_get_languages,
				self._on_languages_error
			)
		else:
			on_success(self._languages)

	def get_source(self, source, langId = None):
		key = (source, langId)
		if key in self._sources:
			node = self._sources[key]
		else:
			if source == "radio":
				node = RadioNode(self._connection)
			elif source == "conferences":
				assert langId is not None
				node = ConferencesNode(self._connection, langId)
			else:
				raise NotImplementedError(source)
			self._sources[key] = node

		return node

	@misc_utils.log_exception(_moduleLogger)
	def _on_get_languages(self, languages):
		assert self._languages is None
		assert self._languagesRequest is not None
		r = self._languagesRequest
		self._languagesRequest = None
		self._languages = languages
		r[0](self._languages)

	@misc_utils.log_exception(_moduleLogger)
	def _on_languages_error(self, e):
		assert self._languages is None
		assert self._languagesRequest is not None
		r = self._languagesRequest
		self._languagesRequest = None
		r[1](self._languages)


class Node(object):

	def __init__(self, connection, parent, data):
		self._connection = connection
		self._parent = weakref.ref(parent) if parent is not None else None
		self._data = data
		self._children = None

	def get_children(self, on_success, on_error):
		if self._children is None:
			self._get_children(on_success, on_error)
		else:
			on_success(self._children)

	def get_parent(self):
		if self._parent is None:
			raise RuntimeError("")
		parent = self._parent()
		return parent

	def get_properties(self):
		return self._data

	def is_leaf(self):
		raise NotImplementedError("")

	def _get_children(self, on_success, on_error):
		raise NotImplementedError("")


class ParentNode(Node):

	def __init__(self, connection, parent, data):
		Node.__init__(self, connection, parent, data)
		self._request = None

	def is_leaf(self):
		return False

	def _get_children(self, on_success, on_error):
		assert self._request is None
		assert self._children is None
		self._request = on_success, on_error

		func, args, kwds = self._get_func()

		self._connection.download(
			func,
			self._on_success,
			self._on_error,
			args,
			kwds,
		)

	def _get_func(self):
		raise NotImplementedError()

	def _create_child(self, data):
		raise NotImplementedError()

	@misc_utils.log_exception(_moduleLogger)
	def _on_success(self, data):
		r = self._request
		self._request = None
		try:
			self._children = [
				self._create_child(child)
				for child in data
			]
		except Exception, e:
			_moduleLogger.exception("Translating error")
			self._children = None
			r[1](e)
		else:
			r[0](self._children)

	@misc_utils.log_exception(_moduleLogger)
	def _on_error(self, error):
		r = self._request
		self._request = None
		r[1](error)


class LeafNode(Node):

	def __init__(self, connection, parent, data):
		Node.__init__(self, connection, parent, data)

	def is_leaf(self):
		return True

	def _get_children(self, on_success, on_error):
		raise RuntimeError("Not is a leaf")


class RadioNode(ParentNode):

	def __init__(self, connection):
		ParentNode.__init__(self, connection, None, {})

	def _get_func(self):
		return "get_radio_channels", (), {}

	def _create_child(self, data):
		return RadioChannelNode(self._connection, self, data)


class RadioChannelNode(LeafNode):

	def __init__(self, connection, parent, data):
		LeafNode.__init__(self, connection, parent, data)
		self._extendedData = {}
		self._request = None

	def get_programming(self, date, on_success, on_error):
		date = date.strftime("%Y-%m-%d")
		try:
			programming = self._extendedData[date]
		except KeyError:
			self._get_programming(date, on_success, on_error)
		else:
			on_success(programming)

	def _get_programming(self, date, on_success, on_error):
		assert self._request is None
		assert date not in self._extendedData
		self._request = on_success, on_error, date

		self._connection.download(
			"get_radio_channel_programming",
			self._on_success,
			self._on_error,
			(self._data["id"], date),
			{},
		)

	@misc_utils.log_exception(_moduleLogger)
	def _on_success(self, data):
		r = self._request
		date = r[2]
		self._request = None
		try:
			self._extendedData[date] = [
				child
				for child in data
			]
		except Exception, e:
			_moduleLogger.exception("Translating error")
			del self._extendedData[date]
			r[1](e)
		else:
			r[0](self._extendedData[date])

	@misc_utils.log_exception(_moduleLogger)
	def _on_error(self, error):
		r = self._request
		self._request = None
		r[1](error)


class ConferencesNode(ParentNode):

	def __init__(self, connection, langId):
		ParentNode.__init__(self, connection, None, {})
		self._langId = langId

	def _get_func(self):
		return "get_conferences", (self._langId, ), {}

	def _create_child(self, data):
		return ConferenceNode(self._connection, self, data)


class ConferenceNode(ParentNode):

	def __init__(self, connection, parent, data):
		ParentNode.__init__(self, connection, parent, data)

	def _get_func(self):
		return "get_conference_sessions", (self._data["id"], ), {}

	def _create_child(self, data):
		return SessionNode(self._connection, self, data)


class SessionNode(ParentNode):

	def __init__(self, connection, parent, data):
		ParentNode.__init__(self, connection, parent, data)

	def _get_func(self):
		return "get_conference_talks", (self._data["id"], ), {}

	def _create_child(self, data):
		return TalkNode(self._connection, self, data)


class TalkNode(LeafNode):

	def __init__(self, connection, parent, data):
		LeafNode.__init__(self, connection, parent, data)
