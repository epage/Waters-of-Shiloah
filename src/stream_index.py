import weakref
import logging

import util.misc as misc_utils
from util import go_utils
import backend


_moduleLogger = logging.getLogger(__name__)


SOURCE_RADIO = "radio"
SOURCE_CONFERENCES = "conferences"
SOURCE_MAGAZINES = "magazines"
SOURCE_SCRIPTURES = "scriptures"


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
			if source == SOURCE_RADIO:
				node = RadioNode(self._connection)
			elif source == SOURCE_CONFERENCES:
				assert langId is not None
				node = ConferencesNode(self._connection, langId)
			elif source == SOURCE_MAGAZINES:
				assert langId is not None
				node = MagazinesNode(self._connection, langId)
			elif source == SOURCE_SCRIPTURES:
				assert langId is not None
				node = ScripturesNode(self._connection, langId)
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
		r[1](e)


class Node(object):

	def __init__(self, connection, parent, data, id):
		self._connection = connection
		self._parent = weakref.ref(parent) if parent is not None else None
		self._data = data
		self._children = None
		self._id = id

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

	@property
	def title(self):
		raise NotImplementedError("On %s" % type(self))

	@property
	def id(self):
		return self._id

	def is_leaf(self):
		raise NotImplementedError("")

	def _get_children(self, on_success, on_error):
		raise NotImplementedError("")


class ParentNode(Node):

	def __init__(self, connection, parent, data, id):
		Node.__init__(self, connection, parent, data, id)

	def is_leaf(self):
		return False

	def _get_children(self, on_success, on_error):
		assert self._children is None

		func, args, kwds = self._get_func()

		self._connection.download(
			func,
			lambda data: self._on_success(data, on_success, on_error),
			on_error,
			args,
			kwds,
		)

	def _get_func(self):
		raise NotImplementedError()

	def _create_child(self, data, id):
		raise NotImplementedError()

	@misc_utils.log_exception(_moduleLogger)
	def _on_success(self, data, on_success, on_error):
		try:
			self._children = [
				self._create_child(child, i)
				for i, child in enumerate(data)
			]
		except Exception, e:
			_moduleLogger.exception("Translating error")
			self._children = None
			on_error(e)
		else:
			on_success(self._children)


class LeafNode(Node):

	def __init__(self, connection, parent, data, id):
		Node.__init__(self, connection, parent, data, id)

	def is_leaf(self):
		return True

	@property
	def can_navigate(self):
		raise NotImplementedError("On %s" % type(self))

	@property
	def subtitle(self):
		raise NotImplementedError("On %s" % type(self))

	@property
	def uri(self):
		raise NotImplementedError("On %s" % type(self))

	def _get_children(self, on_success, on_error):
		raise RuntimeError("Not is a leaf")


class RadioNode(ParentNode):

	def __init__(self, connection):
		ParentNode.__init__(self, connection, None, {}, SOURCE_RADIO)

	@property
	def title(self):
		return "Radio"

	def _get_func(self):
		return "get_radio_channels", (), {}

	def _create_child(self, data, id):
		return RadioChannelNode(self._connection, self, data, id)


class RadioChannelNode(LeafNode):

	def __init__(self, connection, parent, data, id):
		LeafNode.__init__(self, connection, parent, data, id)
		self._extendedData = {}
		self._request = None

	@property
	def can_navigate(self):
		return False

	@property
	def title(self):
		return "Radio"

	@property
	def subtitle(self):
		return ""

	@property
	def uri(self):
		return self._data["url"]

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
		ParentNode.__init__(self, connection, None, {}, SOURCE_CONFERENCES)
		self._langId = langId

	@property
	def title(self):
		return "Conferences"

	def _get_func(self):
		return "get_conferences", (self._langId, ), {}

	def _create_child(self, data, id):
		return ConferenceNode(self._connection, self, data, id)


class ConferenceNode(ParentNode):

	def __init__(self, connection, parent, data, id):
		ParentNode.__init__(self, connection, parent, data, id)

	@property
	def title(self):
		return self._data["title"]

	def _get_func(self):
		return "get_conference_sessions", (self._data["id"], ), {}

	def _create_child(self, data, id):
		return SessionNode(self._connection, self, data, id)


class SessionNode(ParentNode):

	def __init__(self, connection, parent, data, id):
		ParentNode.__init__(self, connection, parent, data, id)

	@property
	def title(self):
		return self._data["title"]

	def _get_func(self):
		return "get_conference_talks", (self._data["id"], ), {}

	def _create_child(self, data, id):
		return TalkNode(self._connection, self, data, id)


class TalkNode(LeafNode):

	def __init__(self, connection, parent, data, id):
		LeafNode.__init__(self, connection, parent, data, id)

	@property
	def can_navigate(self):
		return True

	@property
	def title(self):
		return self._data["title"]

	@property
	def subtitle(self):
		speaker = self._data["speaker"]
		if speaker is not None:
			return speaker
		else:
			return ""

	@property
	def uri(self):
		return self._data["url"]


class MagazinesNode(ParentNode):

	def __init__(self, connection, langId):
		ParentNode.__init__(self, connection, None, {}, SOURCE_MAGAZINES)
		self._langId = langId

	@property
	def title(self):
		return "Magazines"

	def _get_func(self):
		return "get_magazines", (self._langId, ), {}

	def _create_child(self, data, id):
		return MagazineNode(self._connection, self, data, id)


class MagazineNode(ParentNode):

	def __init__(self, connection, parent, data, id):
		ParentNode.__init__(self, connection, parent, data, id)

	@property
	def title(self):
		return self._data["title"]

	def _get_func(self):
		return "get_magazine_issues", (self._data["id"], ), {}

	def _create_child(self, data, id):
		return IssueNode(self._connection, self, data, id)


class IssueNode(ParentNode):

	def __init__(self, connection, parent, data, id):
		ParentNode.__init__(self, connection, parent, data, id)

	@property
	def title(self):
		return self._data["title"]

	def _get_func(self):
		return "get_magazine_articles", (self._data["id"], ), {}

	def _create_child(self, data, id):
		return ArticleNode(self._connection, self, data, id)


class ArticleNode(LeafNode):

	def __init__(self, connection, parent, data, id):
		LeafNode.__init__(self, connection, parent, data, id)

	@property
	def can_navigate(self):
		return True

	@property
	def title(self):
		return self._data["title"]

	@property
	def subtitle(self):
		speaker = self._data["author"]
		if speaker is not None:
			return speaker
		else:
			return ""

	@property
	def uri(self):
		return self._data["url"]


class ScripturesNode(ParentNode):

	def __init__(self, connection, langId):
		ParentNode.__init__(self, connection, None, {}, SOURCE_SCRIPTURES)
		self._langId = langId

	@property
	def title(self):
		return "Scriptures"

	def _get_func(self):
		return "get_scriptures", (self._langId, ), {}

	def _create_child(self, data, id):
		return ScriptureNode(self._connection, self, data, id)


class ScriptureNode(ParentNode):

	def __init__(self, connection, parent, data, id):
		ParentNode.__init__(self, connection, parent, data, id)

	@property
	def title(self):
		return self._data["title"]

	def _get_func(self):
		return "get_scripture_books", (self._data["id"], ), {}

	def _create_child(self, data, id):
		return BookNode(self._connection, self, data, id)


class BookNode(ParentNode):

	def __init__(self, connection, parent, data, id):
		ParentNode.__init__(self, connection, parent, data, id)

	@property
	def title(self):
		return self._data["title"]

	def _get_func(self):
		return "get_scripture_chapters", (self._data["id"], ), {}

	def _create_child(self, data, id):
		return ChapterNode(self._connection, self, data, id)


class ChapterNode(LeafNode):

	def __init__(self, connection, parent, data, id):
		LeafNode.__init__(self, connection, parent, data, id)

	@property
	def can_navigate(self):
		return True

	@property
	def title(self):
		return self._data["title"]

	@property
	def subtitle(self):
		return ""

	@property
	def uri(self):
		return self._data["url"]


def walk_ancestors(node):
	while True:
		yield node
		try:
			node = node.get_parent()
		except RuntimeError:
			return


def common_paths(targetNode, currentNode):
	targetNodePath = list(walk_ancestors(targetNode))
	targetNodePath.reverse()
	currentNodePath = list(walk_ancestors(currentNode))
	currentNodePath.reverse()

	ancestors = []
	descendants = []

	for i, (t, c) in enumerate(zip(targetNodePath, currentNodePath)):
		if t is not c:
			return ancestors, None, descendants
		ancestors.append(t)

	descendants.extend(
		child
		for child in targetNodePath[i+1:]
	)

	return ancestors, currentNode, descendants


class AsyncWalker(object):

	def __init__(self, func):
		self._func = func
		self._run = None

	def start(self, *args, **kwds):
		assert self._run is None
		self._run = self._func(*args, **kwds)
		node = self._run.send(None) # priming the function
		node.get_children(self.on_success, self.on_error)

	@misc_utils.log_exception(_moduleLogger)
	def on_success(self, children):
		_moduleLogger.debug("Processing success for: %r", self._func)
		try:
			node = self._run.send(children)
		except StopIteration, e:
			pass
		else:
			node.get_children(self.on_success, self.on_error)

	@misc_utils.log_exception(_moduleLogger)
	def on_error(self, error):
		_moduleLogger.debug("Processing error for: %r", self._func)
		try:
			node = self._run.throw(error)
		except StopIteration, e:
			pass
		else:
			node.get_children(self.on_success, self.on_error)


def get_next(node, on_success, on_error):
	try:
		assert node.is_leaf(), node

		# Find next branch
		childNode = node
		while True:
			parent = childNode.get_parent()
			siblings = yield parent
			for i, sibling in enumerate(siblings):
				if sibling is childNode:
					break
			i += 1
			if i < len(siblings):
				sibling = siblings[i]
				break
			else:
				childNode = parent

		# dig into that branch to find the first leaf
		nodes = [sibling]
		while nodes:
			child = nodes.pop(0)
			if child.is_leaf():
				on_success(child)
				return
			children = yield child
			nodes[0:0] = children
		raise RuntimeError("Ran out of nodes when hunting for first leaf of %s" % node)
	except Exception, e:
		on_error(e)


def get_previous(node, on_success, on_error):
	try:
		assert node.is_leaf(), node

		# Find next branch
		childNode = node
		while True:
			parent = childNode.get_parent()
			siblings = yield parent
			for i, sibling in enumerate(siblings):
				if sibling is childNode:
					break
			i -= 1
			if 0 <= i:
				sibling = siblings[i]
				break
			else:
				childNode = parent

		# dig into that branch to find the first leaf
		nodes = [sibling]
		while nodes:
			child = nodes.pop(-1)
			if child.is_leaf():
				on_success(child)
				return
			children = yield child
			nodes[0:0] = children
		raise RuntimeError("Ran out of nodes when hunting for first leaf of %s" % node)
	except Exception, e:
		on_error(e)
