# -*- coding: utf-8 -*-
#
# (c) 2016 Nuneo, http://www.nuneo.top
#
# This file is part of Ema.
#
# Ema is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# Ema is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ema.  If not, see <http://www.gnu.org/licenses/>.
#

from __future__ import print_function

import os
import json
import urllib2
import settings as AppSettings
from datetime import datetime, timedelta

# Missing require by Kivy on Linux
try:
    import gi
    gi.require_version('Gtk', '3.0')
except:
    pass

import kivy
kivy.require('1.0.6')


from kivy.app import App
from kivy.logger import Logger
from kivy.uix.settings import Settings
from kivy.uix.boxlayout import BoxLayout
from ConfigParser import NoOptionError

from kyurlrequest import KyUrlRequest


class KyModule(BoxLayout):
    
    """
    A BoxLayout Module with binded properties and a call method.
    
    A module can be real or fake. In case of fake module, the call
    don't do anything but app don't raise any error.
    
    """
    
    name = "KyModule"
    ids = {}
    congregation = ""
    meeting_is_running = {}
    lang = ""
    font = ""
    save_path = os.path.expanduser(os.path.join("~", ".ema", ""))
    
    def __init__(self, **kwargs):
        if not os.path.isdir(self.save_path):
            os.mkdir(self.save_path)
        super(KyModule, self).__init__(**kwargs)
        self._binds = {}
        self.app = App.get_running_app()
        self.config = self.app.config

    def call(self, name, *args):
        if hasattr(self, "call_"+name):
            return getattr(self, "call_"+name)(*args)
    
    def get(self, name):
        if name in self.ids:
            return self.ids[name]
    
    def get_config(self, section="", key=""):
        """Return config value from
        if no key => congregation:key
        if section and key =>section:key."""
        if not key:
            key = section
            section = KyModule.congregation
        try:
            value = self.config.get(section, key)
        except NoOptionError:
            return ""
        Logger.info("Config: %s:%s = %r" % (section, key, value))
        return value.encode("utf-8")

    def set_config(self, value, section="", key=""):
        """Save config value
        if no key => congregation:key
        if section and key =>section:key."""
        if not key:
            key = section
            section = KyModule.congregation
        value = self.config.set(section, key, value.decode("utf-8"))
        Logger.info("SET Config: %s:%s = %r" % (section, key, value))
        self.config.write()

    def update_lang_and_font(self):
        """Update language and font used by the app."""
        self.lang = self.get_config("lang")
        fonts = self.get_config("main", "fonts")
        for font in fonts.split("\n"):
            sfont = font.split(" ")
            if self.lang == sfont[0]:
                self.font = sfont[1]

    def update_meeting_informations(self):
        """Update informations about meeting"""
        today = datetime.today()
        now = datetime.now()
        #now = datetime(2016, 11, 16, 17, 45, 0)
        weekday = today.weekday()
        #weekday = 5
        if weekday in (5, 6):
            meeting = "meeting_we_"
        else:
            meeting = "meeting_w_"

        congegation_with_meeting = None
        last_diff = timedelta(hours=24)
        for section in self.config.sections():
            if section[:12] == "congregation":
                #Always provide a congregation
                if not congegation_with_meeting:
                    congegation_with_meeting = section
                day = self.get_config(section, meeting+"day")
                hour = self.get_config(section, meeting+"hour")
                last_congregation = section
                if int(day) == weekday:
                    shour = hour.split(":")
                    meeting_start = datetime(
                        today.year,
                        today.month,
                        today.day,
                        int(shour[0]),
                        int(shour[1]), 0)
                    meeting_end = meeting_start + timedelta(
                        hours=2, minutes=10)
                    
                    if now >= meeting_start and now <= meeting_end:
                        last_diff = 0
                        congegation_with_meeting = section
                    elif (now < meeting_start
                        and (meeting_start - now) < last_diff):
                            last_diff = meeting_start - now
                            congegation_with_meeting = section

        Logger.info(self.name+": Selected congregation: %s"
            % self.config.get(congegation_with_meeting, "name"))
        Logger.info(self.name+": Meeting type: %s" % meeting)
            
        KyModule.congregation = congegation_with_meeting
        KyModule.meeting_type = meeting
        KyModule.meeting_is_running = last_diff == 0

    def _url_request(self, url, callback=None, callback_if_fail=None):
        req = KyUrlRequest(self.name)
        req.open(url, callback, callback_if_fail)


class KyApp(App):
    
    """
    The App base class with pre-build settings.
    
    """
    
    config_changes_triggers = {}
    settings_cls = Settings
    use_kivy_settings = False

    def bind_to(self, src, obj, dest):
        self.bind(**{src: obj.property(dest).set})

    def get_application_config(self):
        """Setup the config filename. A single file for all apps."""
        return super(KyApp, self).\
            get_application_config('settings/ema.ini')

    def build_config(self, config):
        """Build config using json file for default values."""
        with open("settings/default_settings.json", "rb") as f:
            default_settings = json.load(f)

        for section, values in default_settings.items():
            config.setdefaults(section, values)

    def build_settings(self, settings):
        """Register types for settings."""
        AppSettings.register_types(settings)

    def add_config_change_trigger(self, section, key, callback):
        """Add trigger for changes in a section/key."""
        self.config_changes_triggers[section+"::"+key] = callback

    def on_config_change(self, config, section, key, value):
        """React to changes on config."""
        Logger.info("EmaSettings: config changed %s, %s, %s, %r"
            % (config, section, key, value))
        kw = section+"::"+key
        if kw in self.config_changes_triggers:
            self.config_changes_triggers[kw](config, value)
            #self.meeting_infos.update_urls(value.split("\n"))


