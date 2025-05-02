import logging
import typing as t
from flask import Flask

from gunicorn.app.base import BaseApplication

from gunicorn.config import Config


class FlaskHammerGunicornApp(BaseApplication):
    cfg: Config  # Set by super().__init__() -> do_load_config() -> load_default_config()

    def __init__(self, flask_app: Flask, options=None):
        self._options = options or dict()
        self.application = flask_app
        super().__init__()

    def set_logger(self, logger: logging.Logger):
        self.logger = logger

    def load_config(self):
        config = dict()

        # Merge init options on top of defaults

        for key, value in self._options.items():
            if key in self.cfg.settings and value is not None:
                config[key] = value

        for key, value in config.items():
            self.cfg.set(key.lower(), value)

    def load(self):
        return self.application

    @classmethod
    def run_with_config(cls, flask_app: Flask, options: dict):
        return cls(flask_app, options).run()
