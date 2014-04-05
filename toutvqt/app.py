import os
import sys
import logging
import platform
from pkg_resources import resource_filename
from PyQt4 import uic
from PyQt4 import Qt
from toutvqt.main_window import QTouTvMainWindow
from toutvqt.settings import QTouTvSettings
from toutvqt.settings import SettingsKeys
from toutvqt import config
import toutv.client


class _QTouTvApp(Qt.QApplication):
    def __init__(self, args):
        super().__init__(args)

        self._proxies = None

        self.setOrganizationName(config.ORG_NAME)
        self.setApplicationName(config.APP_NAME)

        self._setup_client()
        self._setup_ui()
        self._setup_settings()
        self._start()

    def get_settings(self):
        return self._settings

    def get_proxies(self):
        return self._proxies

    def _start(self):
        self.main_window.start()

    def _setup_ui(self):
        self.main_window = QTouTvMainWindow(self, self._client)

    def _setup_client(self):
        self._client = toutv.client.Client()

    def _setup_settings(self):
        # Create a default settings
        self._settings = QTouTvSettings()

        # Connect the signal between main window and the settings
        self.main_window.settings_accepted.connect(
            self._settings.apply_settings)

        # Connect the signal between settings and us
        self._settings.setting_item_changed.connect(self._setting_item_changed)

        # Read the settings from disk
        self._settings.read_settings()

    def _on_setting_http_proxy_changed(self, value):
        value = value.strip()
        if not value:
            proxies = None
        else:
            proxies = {
                'http': value,
                'https': value
            }

        self._proxies = proxies
        self._client.set_proxies(proxies)

    def _on_setting_dl_dir_changed(self, value):
        # Create output directory if it doesn't exist
        if not os.path.exists(value):
            try:
                os.makedirs(value)
            except:
                # Ignore; should fail later
                pass

    def _setting_item_changed(self, key, value):
        if key == SettingsKeys.NETWORK_HTTP_PROXY:
            self._on_setting_http_proxy_changed(value)
        elif key == SettingsKeys.FILES_DOWNLOAD_DIR:
            self._on_setting_dl_dir_changed(value)


def _register_sigint():
    if platform.system() == 'Linux':
        import signal
        signal.signal(signal.SIGINT, signal.SIG_DFL)


def _configure_logging():
    logging.basicConfig(level=logging.DEBUG)


def run():
    _configure_logging()
    _register_sigint()
    app = _QTouTvApp(sys.argv)

    return app.exec_()
