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

import os
import glob
import time
import shutil
import random
import fnmatch
import urllib2
from collections import deque, OrderedDict
import kivy
kivy.require('1.0.6')

from kivy.app import App
from kivy.clock import Clock
from kivy.properties import ObjectProperty,\
    StringProperty, NumericProperty
from kivy.logger import Logger
from kivy.uix.popup import Popup
from kivy.lang import Builder
from kivy.uix.settings import Settings
from kivy.core.audio import SoundLoader
from kivy.uix.boxlayout import BoxLayout

from libs.kyapp import KyApp, KyModule
from libs.kyhtmlparser import KyHtmlParser

class SongInput(kivy.uix.textinput.TextInput):
    
    """
    Customized Input used to limit number of chars.
    
    """
    module = ObjectProperty(None)
    max_chars = 3
    mp3 = None
    
    def on_focus(self, textinput, have_focus):
        if not self.mp3:
            self.mp3 = App.get_running_app().mp3player

        if not have_focus:
            return
        self.popup = popup = Builder.load_file('kv/numpad.kv')
        self.select_number = popup.ids["select_number"]
        popup.title = "Numéro de cantique"
        self.select_number.text = textinput.text
        self.select_text = self.popup.ids["select_text"]
        songs = OrderedDict(sorted(self.mp3.songs.items()))
        self.select_number.values = songs
        self.select_number.bind(on_press = self.spinner_to_darkness)
        self.select_number._dropdown.bind(
            on_dismiss = self.spinner_to_lightness)
        self.select_number.bind(
            text = lambda obj, text: self.validate_num(text))
        self.popup.background_color = (0, 0, 0, 0)
        self.validate_num(textinput.text)
        for n in range(10):
            b = popup.ids["n"+str(n)]
            b.bind(on_press=self.keynum_pressed)
        b = popup.ids["nDel"]
        b.bind(on_press=self.del_pressed)
        b = popup.ids["nOk"]
        b.text = "Valider"
        b.bind(on_press=lambda *x: self.ok_pressed(textinput))
        popup.open()

    def spinner_to_darkness(self, *args):
        self.popup.background_color = (1, 0, 0, 0)
    
    def spinner_to_lightness(self, *args):
        self.popup.background_color = (0, 0, 0, 0)

    def keynum_pressed(self, button):
        if len(self.select_number.text) > 2:
            return
        self.select_number.text = self.validate_num(
            self.select_number.text + button.text)

    def del_pressed(self, button):
        if len(self.select_number.text) < 1:
            return
        self.select_number.text = self.validate_num(
            self.select_number.text[:-1])

    def ok_pressed(self, inputtext):
        self.popup.dismiss()
        inputtext.text = self.select_number.text
        inputtext.dispatch("on_text_validate")

    def validate_num(self, num):
        song_name = self.mp3.get_name_of_song_number(num)
        print(song_name)
        if song_name[0] == "null":
            self.select_text.text = song_name[1]
        elif song_name[0] or num == "" or num == "0" or num == "00":
            self.select_text.text = \
                "[font=data/fonts/"+self.mp3.font\
                +"]"+song_name[1]+"[/font]"
            return num
        return self.select_number.text
            

    def insert_text(self, substring, from_undo=False):
        """React to insertion of text."""
        if (not from_undo and
                (len(self.text)+len(substring) > self.max_chars)):
            return
        final = ""
        for c in substring:
            if ord(c) >= ord("0") and ord(c) <= ord("9"):
                final+=c
        
        self.song_number
        super(SongInput, self).insert_text(final, from_undo)


class SelectSing(BoxLayout):
    
    """
    Widget ysed to select a song to sing.
    
    """
    
    initial_image = StringProperty("")


class Mp3Player(KyModule):
    
    """
    Mp3Player Module. Used to manage songs.
    
    """
    
    # Useful links for download i18n songs titles
    JW_1TO135_MP3 = "https://www.jw.org/apps/GETPUBMEDIALINKS?\
output=html&pub=iasnm&fileformat=MP3%2CAAC&\
alllangs=0&langwritten="
    JW_A136_MP3 = "https://www.jw.org/apps/GETPUBMEDIALINKS?\
output=html&pub=snnw&fileformat=MP3%2CAAC&\
alllangs=0&langwritten="
    
    SONG_NAME_NOT_FOUND =  u"[color=#FFC0CB]\
En attente de chargement des noms des cantiques[/color]"
    
    
    infos = StringProperty("")
    progress = NumericProperty(0)
    max_progress = NumericProperty(100)
    congregation = StringProperty("")

    #Font used for display of songs titles
    #  (we need it for unicode chars)
    font = "DejaVuSansCondensed.ttf"
    
    #List of availabled songs by lang
    songs = {}

    #The 3 songs we will use on the meeting
    sings = [None, None, None]
    sing = 0
    sing_colors = ("", "")
    sing_slot = 0
    
    player = None
    updater = None
    player_binduid = None
    pause_pos = 0
    congreg_id = 0
    
    def init(self):
        """Initialize Mp3Player module."""
        Logger.info("MP3: Init")
        self.infos = u"[color=#557777]\
- Mise à jour des noms des cantiques depuis JW.ORG -[/color]"
        self. MP3PATH = os.path.expanduser(
            os.path.normcase(self.get_config("mp3", "songs_path")))
        self.update_song_names()
        if not self.meeting_is_running:
            Clock.schedule_once(self.play_random, 2)
            self.loaded_songs_infos = ""
        else:
            self.loaded_songs_infos = \
                u"[color=#555555]-- Réunion en cours --[/color]"

        self.init_finished = True
            
    def _parse_songs_list(self, request, result, newsongs=True):
        """Parse songs list downloaded from Jw.org."""
        parser = KyHtmlParser(result)
        parser.findall_attr({"class": "linkDnld"}).gettext()
        mp3_links = parser.parse()
        
        songs = ""        
        for link in mp3_links:
            if " " in link:
                number, title = link.split(" ", 1)
                number = number[:3]
                if number.isdigit():
                    songs = songs + number + " " + title + "\n"

        if newsongs:
            self._save_song_names(songs)
        else:
            self._save_song_names(None, songs)
        self.update_songs(False)

    def _url_request_failed(self, request, result):
        self._update_song_names()

    def _set_infos(self, colors, sing):
        """Display informations about the current song."""
        if not sing:
            return
        
        if self.lang in self.songs and sing in self.songs[self.lang]:
            title = self.songs[self.lang][sing]
        else:
            title = self.SONG_NAME_NOT_FOUND

        self.sing_colors = colors
        text = "[color="+colors[0]+"]"+sing\
            +"[/color] [color="+colors[1]+"]"\
            +title+"[/color]"
        self.infos = (
            u"[font=data/fonts/"+self.font+"]"+text+u"[/font]"
            )

    def _save_song_names(self, newsongs="", firstsongs=""):
        """Update song names from Wol using lang of congregation."""
        songs = firstsongs
        if not firstsongs:
            if os.path.isfile(self.save_path+"135_songs_"+self.lang+".lst"):
                songs = open(self.save_path+"135_songs_"+self.lang+".lst",
                    "rb").read().decode("utf-8")
        else:
            open(self.save_path+"135_songs_"+self.lang+".lst",
                "wb").write(firstsongs.encode("utf-8"))
        
        if not newsongs:
            if os.path.isfile(self.save_path+"new_songs_"+self.lang+".lst"):
                songs = songs + open(self.save_path+"new_songs_"+self.lang+".lst",
                    "rb").read().decode("utf-8")
        else:
            open(self.save_path+"new_songs_"+self.lang+".lst",
                "wb").write(newsongs.encode("utf-8"))
            songs = songs + newsongs
        
        if songs:
            if not self.lang in self.songs:
                self.songs[self.lang] = {}
            for song in songs.split("\n"):
                if song:
                    number, title = song.split(" ", 1)
                    self.songs[self.lang][number] = title
        
        if self.loaded_songs_infos:
            self.infos = self.loaded_songs_infos

    def update_songs(self, update_names=True):
        """Update song names and current sing with new lang."""
        Logger.info("MP3: Update song names and current")
        
        if update_names:
            #Update song names with new lang setting
            self.update_song_names()
        
        #Update current sing 
        self._set_infos(self.sing_colors, self.sing)
        slot = 0
        for sing in self.sings:
            if sing:
                widget, title, selector, filename, number = sing
                self.validate_song_number(
                    widget, slot, number, selector)
            slot = slot + 1
        
    def update_song_names(self):
        """Start updating of song names (first time, dl from jw.org)."""
        self.update_lang_and_font()
        if not self.lang in self.songs or not self.songs[self.lang]: # Only dl first time
            self._url_request(
                self.JW_A136_MP3+self.lang,
                lambda req, res: self._parse_songs_list(req, res, True),
                self._url_request_failed)
            self._url_request(
                self.JW_1TO135_MP3+self.lang,
                lambda req, res: self._parse_songs_list(req, res, False),
                self._url_request_failed)
        else:
            self._save_song_names()

    def get_name_of_song_number(self, number, check_mp3=True):
        """Get the name of a song by the number."""
        if not number or number == "0" or number == "00":
            return (None, "")
            
        default = (None, 
            "[b][color=#FF9797]\
- Mauvais cantique... Bah alors ? -[/color][/b]")
        try:
            num = "%.03d" % int(number)
        except:
            return default

        if self.songs and self.lang in self.songs:
            if not num in self.songs[self.lang]:
                return default
            song_title = self.songs[self.lang][num]
        else:
            song_title = self.SONG_NAME_NOT_FOUND
        
        for mp3 in glob.glob(self.MP3PATH+"/*"+num+".mp3"):
            return (mp3, " "+song_title)
        
        return default

    def play(self, filename, random=False):
        """Play mp3 file."""
        Logger.info("MP3: Playing %s ..." % filename)
        if self.player:
            self.pause_pos = 0
            self.player.unbind_uid("on_stop", self.player_binduid)
            self.player.stop()
            self.player.unload()
        self.player = SoundLoader.load(filename)
        if self.player:
            if random:
                self.player_binduid = self.player.fbind(
                    "on_stop",
                    self.play_random)
            else:
                self.player_binduid = self.player.fbind(
                    "on_stop",
                    self.next_slot_sing)
            self.player.play()
            self.updater = Clock.schedule_interval(
                self.update_pos, 0.5)
            self._set_infos(("#A0FF8A", "#FFFFFF"), self.sing)

    def pause(self):
        """Pause mp3 file playing."""
        Logger.info("MP3: Pause")
        if self.player and not self.pause_pos:
            self.pause_pos = self.player.get_pos()
            self.player.unbind_uid("on_stop", self.player_binduid)
            self.player.stop()
            self._set_infos(("#FF556A", "#FF556A"), self.sing)

    def resume(self):
        """Resume mp3 file playing."""
        Logger.info("MP3: Resume")
        if self.player:
            self.player_binduid = self.player.fbind(
                "on_stop",
                self.next_slot_sing)
            self.volume = 0
            self.player.play()
            time.sleep(0.1)
            self.player.seek(self.pause_pos)
            self.volume = 1
            self.pause_pos = 0
            self._set_infos(("#A0FF8A", "#FFFFFF"), self.sing)
            
    def stop(self):
        """Stop mp3 file playing."""
        Logger.info("MP3: Stop")
        if self.player:
            self.pause_pos = 0
            self.player.unbind_uid("on_stop", self.player_binduid)
            self.player.stop()
            self.player.unload()
            self.player = None
            self.sing = 0
            if self.updater:
                self.updater.cancel()
                self.updater = None
            self.infos = "[color=#555555]\
- Pas de cantique en cours -[/color]"

    def update_pos(self, dt):
        """Update the playing progress bar."""
        if self.player and not self.pause_pos:
            self.max_progress = self.player.length
            self.progress = self.player.get_pos()

    def get_state(self):
        """Get the state of the play."""
        if self.pause_pos:
            return "pause"
        if self.player:
            return self.player.state
        return "stop"

    def play_random(self, *args):
        """Select a song number on the playlist and play it.
        
        Each congregation have the own playlist.
        """
        print(self.save_path)
        files = []
        if (not self.congregation):
            self.congregation = "congregation1"
        playlist_filename = self.save_path+"playlist_"\
            +self.congregation+".lst"
        if os.path.isfile(playlist_filename):
            with open(playlist_filename, "rb") as f:
                files = f.read().split("\n")
            if files[0] == "":
                files = []
            
        if len(files) == 0:
            Logger.info("MP3: The playlist are empty, building a new")
            files = self.songs.keys()
            random.shuffle(files)

        songs = deque(files)
        song_number = songs.popleft()
        if not song_number.isdigit():
            return
        mp3 = None
        for mp3 in glob.glob(
            self.MP3PATH+"/*%.03d.mp3" % int(song_number)):
                Logger.info("MP3: Random selected: %s" % mp3)
        self.sing = song_number
        if mp3:
            self.play(mp3, True)

        with open(playlist_filename, "wb") as f:
            f.write("\n".join(songs))
        
        
    def validate_song_number(self, widget, slot, number, selector):
        """Validate if the number of song enter by user is right"""
        filename, title = self.get_name_of_song_number(number)
        if slot == self.sing_slot:
            widget.text = "[font=data/fonts/"+self.font\
                +"][color=#FFD78E]"+title+"[/color][/font]"
        else:
            widget.text = "[font=data/fonts/"+self.font+"]"+title\
                +"[/font]"
        self.sings[slot] = (widget, title, selector, filename, number)

    def next_slot_sing(self, *args):
        """Select the next sing slot"""
        Logger.info("MP3: Selected next slot: %s" % self.sings)
        self.stop()
        if self.sings == [None, None, None]:
            return

        slot = self.sing_slot
        next_slot = slot
        while True:
            next_slot += 1
            if next_slot < 0:
                next_slot = 2
            if next_slot > 2:
                next_slot = 0
            if self.sings[next_slot]:
                break

        if next_slot == slot:
            return
        self.sing_slot = next_slot
        self.sings[next_slot][0].text = "[font=data/fonts/"+self.font\
            +"][color=#FFD78E]"\
            +self.sings[next_slot][1]+"[/color][/font]"
        self.sings[next_slot][2].source = "data/images/bullet_go.png"
        
        self.sings[slot][0].text = "[font=data/fonts/"+self.font\
            +"]"+self.sings[slot][1]+"[/font]"
        self.sings[slot][2].source =\
            "atlas://data/images/defaulttheme/action_item"
        
    def play_sing(self):
        filename = None
        if self.get_state() == "pause":
            self.resume()
        elif self.sings[self.sing_slot]:
            widget, title, selector, filename, number \
                = self.sings[self.sing_slot]
        if filename:
            self.sing = "%.03d" % int(number[:3])
            self.play(filename)

class Mp3PlayerApp(KyApp):
    use_kivy_settings = False
    settings_cls = Settings
    ui = None

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
