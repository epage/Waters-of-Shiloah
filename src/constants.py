import os

__pretty_app_name__ = "Waters of Shiloah"
__app_name__ = "watersofshiloah"
__version__ = "1.0.6"
__build__ = 0
__app_magic__ = 0x1AFF5
_data_path_ = os.path.join(os.path.expanduser("~"), ".%s" % __app_name__)
_user_settings_ = "%s/settings.ini" % _data_path_
_cache_path_ = "%s/cache" % _data_path_
_user_logpath_ = "%s/%s.log" % (_data_path_, __app_name__)
