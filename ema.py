#!/usr/bin/env python2
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

import json
from datetime import datetime, timedelta, time

try:
    import colored_traceback
    colored_traceback.add_hook()
except:
    pass

import kivy
kivy.require("1.0.6")

from kivy.app import App
from kivy.clock import Clock
from kivy.logger import Logger
from kivy.config import Config
Config.set("graphics", "width", "1024")
Config.set("graphics", "height", "768")
Config.set("input", "mouse", "mouse,multitouch_on_demand")

from kivy.event import EventDispatcher
from kivy.core.window import Window
from kivy.properties import StringProperty, ObjectProperty
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.actionbar import ActionButton
from kivy.uix.screenmanager import ScreenManager, Screen

# This import order is important on windows systems
from modules.mp3player import Mp3Player
from modules.meetinginfos import MeetingInfos
from modules.elya import Elya

from libs.kyapp import KyApp, KyModule
import version

class EmaUi(FloatLayout):
    """
    Root widget for Ema Graphical Interface
    
    """
    
    status = StringProperty("")
    selected_congregation = StringProperty("")
    time = StringProperty("00:00")
    version = StringProperty(version.EMA_VERSION)

    def log(self, message):
        """Display logs on the window."""
        Logger.info(message)
        if message and self.status:
            self.status = message

class EmaApp(KyApp):
    """
    Ema app
    
    """
    
    kv_directory = "kv"
    kym = ObjectProperty(None)
    congregation = StringProperty("")
    
    def build(self):
        """Build and return user interface."""
        super(EmaApp, self).build()
        self.icon = 'data/images/icon32.png'
        self.emaUi = EmaUi()
        Logger.info('EmaUi: Building...')
        return self.emaUi

    def build_settings(self, settings):
        """Build settings panel."""
        super(EmaApp, self).build_settings(settings)
        settings.add_json_panel('Général', self.config,
                                'settings/main.json')
        
    def connect_widgets(self):
        """Connect widgets of modules (like MeetingInfos with Mp3Player)."""
        Logger.info("Ema: Binding modules...")
        if self.config.get("main", "use_elya"):
            self.elya = self.emaUi.ids['elya']
            self.elya.log = self.emaUi.log
        else:
            self.elya = kyModule()
        
        if self.config.get("main", "use_mp3"):
            self.mp3player = self.emaUi.ids['mp3player']
        else:
            self.mp3player = kyModule()
        
        if  self.config.get("main", "use_meetinginfos"):
            self.meetinginfos = self.emaUi.ids['meetinginfos']
            self.meetinginfos.bind(time=self.emaUi.setter("time"))
            self.meetinginfos.sing1 =\
                self.mp3player.ids["sing1"].ids["sing_input"]
            self.meetinginfos.sing2 =\
                self.mp3player.ids["sing2"].ids["sing_input"]
            self.meetinginfos.sing3 =\
                self.mp3player.ids["sing3"].ids["sing_input"]
        else:
            self.meetinginfos = kyModule()

    def on_select_congregation(self, button):
        """Update widgets when user change the congregation."""
        KyModule.congregation = button.id
        spinner = self.emaUi.ids["congregations"]
        spinner._dropdown.select(None)

        #Update spinner with name of selected congregation
        name = self.config.get(KyModule.congregation, "name")
        spinner.text = " "*(50-len(name))+name

        self.mp3player.update_songs()
        self.meetinginfos.get_program_from_wol()


    def update_congregation_spinner(self):
        """Update the congregation list."""
        spinner = self.emaUi.ids["congregations"]
        for section in self.config.sections():
            if section[:12] == "congregation":
                ab = ActionButton(text=self.config.get(section, "name"))
                ab.id = section
                ab.bind(on_press=self.on_select_congregation)
                spinner.add_widget(ab)
        name = self.config.get(self.kym.congregation, "name")
        spinner.text = " "*(50-len(name))+name


    def get_program(self, *dt):
        self.meetinginfos.get_program_from_wol()
        Clock.schedule_interval(self.meetinginfos.update_time, 1)

    def on_start(self):
        """ Start the app """
        Logger.info('Ema: Starting...')
        self.emaUi.status = "Init..."

        #Kym is the main KyModule (top boxlayout)
        self.kym = self.emaUi.ids['kym']
        self.kym.update_meeting_informations()

        self.connect_widgets()
        self.mp3player.init()
        self.meetinginfos.init()
        
        #Display congregations selector
        self.update_congregation_spinner()
        
        #Clock.schedule_once(
        #    lambda dt: self.elya.connect_sip_account(), 1)

        self.elya.load_contacts()
        #self.elya.connect_ovh_account()
        #self.elya.clean_conference()
        
    def on_stop(self):
        pass
        #self.elya.quit()

if __name__ == '__main__':
    EmaApp().run()

