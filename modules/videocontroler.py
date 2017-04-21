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


import kivy
kivy.require('1.0.6')

from kivy.app import App
from kivy.properties import *
from kivy.uix.settings import Settings
from kivy.uix.boxlayout import BoxLayout

from kivyapp import kivyApp


class VideoControler(BoxLayout):
    infos = StringProperty("")
    progress = NumericProperty(0)
    max_progress = NumericProperty(100)

    congregation = ""
    
    def setLang(self, lang, langcode):
        self.lang = lang

class VideoControlerApp(kivyApp):
    use_kivy_settings = False
    settings_cls = Settings
    ui = None

    def build_config(self, config):
        super(Mp3PlayerApp, self).build_config(config)
        config.update_config("ema.ini")

    def build(self):
        self.ui = Mp3Player()
        return self.ui
    
    def on_start(self):
        super(Mp3PlayerApp, self).on_start()
        self.ui.congregation =  self.congregation
        self.ui.get_song_names()
        Clock.schedule_once(lambda dt: self.ui.play_random(), 1)
    
    def on_stop(self):
        self.ui.stop()

if __name__ == '__main__':
    Mp3PlayerApp().run()
