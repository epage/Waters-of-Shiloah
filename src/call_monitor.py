import logging

import gobject
import dbus
import telepathy

import gtk_toolbox


_moduleLogger = logging.getLogger(__name__)
DBUS_PROPERTIES = 'org.freedesktop.DBus.Properties'


class NewChannelSignaller(object):

	def __init__(self, on_new_channel):
		self._sessionBus = dbus.SessionBus()
		self._on_user_new_channel = on_new_channel

	def start(self):
		self._sessionBus.add_signal_receiver(
			self._on_new_channel,
			"NewChannel",
			"org.freedesktop.Telepathy.Connection",
			None,
			None
		)

	def stop(self):
		self._sessionBus.remove_signal_receiver(
			self._on_new_channel,
			"NewChannel",
			"org.freedesktop.Telepathy.Connection",
			None,
			None
		)

	@gtk_toolbox.log_exception(_moduleLogger)
	def _on_new_channel(
		self, channelObjectPath, channelType, handleType, handle, supressHandler
	):
		connObjectPath = channel_path_to_conn_path(channelObjectPath)
		serviceName = path_to_service_name(channelObjectPath)
		try:
			self._on_user_new_channel(
				self._sessionBus, serviceName, connObjectPath, channelObjectPath, channelType
			)
		except Exception:
			_moduleLogger.exception("Blocking exception from being passed up")


class ChannelClosed(object):

	def __init__(self, bus, conn, chan, on_closed):
		self.__on_closed = on_closed

		chan[telepathy.interfaces.CHANNEL].connect_to_signal(
			"Closed",
			self._on_closed,
		)

	@gtk_toolbox.log_exception(_moduleLogger)
	def _on_closed(self):
		self.__on_closed(self)


class CallMonitor(gobject.GObject):

	__gsignals__ = {
		'call_start' : (
			gobject.SIGNAL_RUN_LAST,
			gobject.TYPE_NONE,
			(),
		),
		'call_end' : (
			gobject.SIGNAL_RUN_LAST,
			gobject.TYPE_NONE,
			(),
		),
	}

	def __init__(self):
		gobject.GObject.__init__(self)
		self._isActive = False
		self._newChannelMonitor = NewChannelSignaller(self._on_new_channel)
		self._channelClosedMonitors = []

	def start(self):
		self._isActive = True
		self._newChannelMonitor.start()

	def stop(self):
		self._isActive = False
		self._newChannelMonitor.stop()

	def _on_new_channel(self, sessionBus, serviceName, connObjectPath, channelObjectPath, channelType):
		if not self._isActive:
			return

		if channelType != telepathy.interfaces.CHANNEL_TYPE_STREAMED_MEDIA:
			return

		cmName = cm_from_path(connObjectPath)
		conn = telepathy.client.Connection(serviceName, connObjectPath)
		try:
			chan = telepathy.client.Channel(serviceName, channelObjectPath)
		except dbus.exceptions.UnknownMethodException:
			_moduleLogger.exception("Client might not have implemented a deprecated method")
			return

		missDetection = ChannelClosed(
			sessionBus, conn, chan, self._on_close
		)
		self._outstandingRequests.append(missDetection)
		if len(self._outstandingRequests) == 1:
			self.emit("call_start")

	def _on_close(self, channelCloseMonitor):
		self._outstandingRequests.remove(channelCloseMonitor)
		if not self._outstandingRequests:
			self.emit("call_stop")


def channel_path_to_conn_path(channelObjectPath):
	"""
	>>> channel_path_to_conn_path("/org/freedesktop/Telepathy/ConnectionManager/theonering/gv/USERNAME/Channel1")
	'/org/freedesktop/Telepathy/ConnectionManager/theonering/gv/USERNAME'
	"""
	return channelObjectPath.rsplit("/", 1)[0]


def path_to_service_name(path):
	"""
	>>> path_to_service_name("/org/freedesktop/Telepathy/ConnectionManager/theonering/gv/USERNAME/Channel1")
	'org.freedesktop.Telepathy.ConnectionManager.theonering.gv.USERNAME'
	"""
	return ".".join(path[1:].split("/")[0:7])


def cm_from_path(path):
	"""
	>>> cm_from_path("/org/freedesktop/Telepathy/ConnectionManager/theonering/gv/USERNAME/Channel1")
	'theonering'
	"""
	return path[1:].split("/")[4]
