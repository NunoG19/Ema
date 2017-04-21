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


import re, sys
import time
import urllib2
import shutil
from string import Template
from datetime import datetime, timedelta

import kivy
kivy.require('1.0.6')

from kivy.app import App
from kivy.properties import ObjectProperty, StringProperty
from kivy.clock import Clock
from kivy.logger import Logger
from kivy.core.window import Window
from kivy.uix.settings import Settings
from kivy.uix.boxlayout import BoxLayout
from kivy.network.urlrequest import UrlRequest


from libs.kyapp import KyApp, KyModule
from libs.kyhtmlparser import KyHtmlParser

class DeltaTemplate(Template):
    delimiter = "%"

def strfdelta(tdelta, fmt):
    hours, rem = divmod(tdelta, 3600)
    minutes, seconds = divmod(rem, 60)
    d = {"H" : "%.2d" % hours,
        "M" : "%.2d" % minutes,
        "S" : "%.2d" % seconds}
    t = DeltaTemplate(fmt)
    return t.substitute(**d)

COMMENT = u"01 min : [font=data/fonts/ema.ttf]\uE80D[/font]"
WARNING_SYMBOL = u"[font=data/fonts/ema.ttf]\uE80C[/font]"
SING_SYMBOL = u"[font=data/fonts/ema.ttf]\uE80B[/font]"
SPEECH_SYMBOL = u"[font=data/fonts/ema.ttf]\uE804[/font]"
RUN_SYMBOL = u"[font=data/fonts/ema.ttf]\uE800[/font]"
    
class MeetingInfos(KyModule):
    
    """
    MeetingInfos Module. Used to display meeting program and timer
    
    """
    
    name = "MeetingInfo"
    wol_urls = {}
    congregation = StringProperty("")
    font = "DejaVuSansCondensed.ttf"
    lang = ""
        
    deltatimes = []
    meetingparts = []
    songs = []
    current_part = 0
    
    wol_prog_errors = 0

    sing1 = ObjectProperty(None)
    sing2 = ObjectProperty(None)
    sing3 = ObjectProperty(None)
    
    parts = StringProperty("???")
    times = StringProperty("???")
    time = StringProperty("00:00")
    offset = StringProperty("00")

    def _insert_time(self, offset, minutes):
        self.deltatimes.insert(len(self.deltatimes)+offset, [minutes])
        
    def _add_time(self, minutes):
        self._insert_time(0, minutes)

    def _insert_part(self, offset, part):
        self.meetingparts.insert(len(self.meetingparts)+offset, part)

    def _add_part(self, part):
        self._insert_part(0, part)


    def init(self):
        """Initialize MeetingInfos module."""
        self.get_program_from_wol()
        Clock.schedule_interval(self.update_time, 1)

    def get_program_from_wol(self, *args):
        """Get the program from Wol using the current language."""
        self.parts = u"[color=#557777]\
- Mise à jour du porgramme de la réunion depuis wol.jw.org -[/color]"
        
        self.update_lang_and_font()
        
        values = self.get_config("main", "wol_paths").split("\n")
        for url in values:
            surl = url.split(" ")
            self.wol_urls[surl[0]] = surl[1]
        url = self.wol_urls[self.lang]+time.strftime("%Y/%m/%d")
        #url = self.wol_urls[lang]+"2016/11/07"

        self._url_request(url,
            self._parse_program_from_wol,
            self._on_get_program_from_wol_error)

    def _on_get_program_from_wol_error(self, req, result):
        self.wol_prog_errors = self.wol_prog_errors + 1
        if self.wol_prog_errors < 3:
            self.parts =\
            u"Erreur, une nouvelle tentative va être lancée dans 3 sec"
            Clock.schedule_once(self.get_program_from_wol, 3)
        else:
            self.parts = "Impossible d'obtenir le programme"

    def _parse_program_from_wol(self, req, result):
        parser = KyHtmlParser(result)
                
        out = ""
        sing_word = ""

        if self.lang == "CHS":
            min_check = r"([^(]*)"\
                +unichr(65288)+"[^0-9]*([0-9]*)[^0-9]*"
        else:
            min_check = r"(.*)\((\d+).min[^0-9A-Z)]*\)"

        self.meetingparts = []
        self.deltatimes = []
        sings = []
    
        if self.meeting_type == "meeting_we_":
            parser.find_attr({"class": "sm"}).find_tag("a").getall()
            watchtower = parser.parse()[0]
            self._add_part(
                u"[color=#FFA500]05 min : "+SING_SYMBOL+"[/color]")
            sings.append("")
            self._add_part(u"30 min : "+SPEECH_SYMBOL)
            if len(watchtower) > 1:
                self._url_request(
                    "http://wol.jw.org"+watchtower[1]["href"],
                    self._load_watchtower,
                    self._load_watchtower_error)
                self._add_part("60 min : "+watchtower[2])
        else:
            parser.findall_attr({"class": "su"}).gettext()
            parser.findall_attr({"class": "sn"}).gettext()
            meeting_program = parser.parse()
            first_line = True
            #print meeting_program
            for line in meeting_program:
                line = line.strip()
                #print("["+line+"]", sing_word)
                if first_line:
                    sing_word, null = line.split(" ", 1)
                    first_line = False
                if line[:len(sing_word)] == sing_word:
                    m = re.search(r"(\d+)", line)
                    self._add_part("[color=#FFA500]05 min : "
                        +sing_word+" "+m.group(1)+"[/color]")
                    self._add_time(5)
                    if len(sings) == 1:
                        if len(self.meetingparts) == 7: 
                            # Have the 3 videos presentations
                            self._insert_part(-2, COMMENT)
                            self._insert_time(-2, 1)
                        else:
                            self._insert_part(-4, COMMENT)
                            self._insert_time(-4, 1)
                            self._insert_part(-3, COMMENT)
                            self._insert_time(-3, 1)
                            self._insert_part(-2, COMMENT)
                            self._insert_time(-2, 1)
                            self._insert_part(-1, COMMENT)
                            self._insert_time(-1, 1)
                    sings.append(m.group(1))
                else:
                    m = re.search(min_check, line)
                    #print ">>>>>>", m.groups()
                    part = m.group(1).strip()
                    if part[-1] == ":":
                        part = part[:-1]
                    if m.group(2):
                        minutes = ("%.2d" % int(m.group(2)))
                        self._add_part(minutes + u" min : " + part)
                        self._add_time(int(m.group(2)))
            self._update_program(sings)

    def _update_program(self, sings):
        if not self.deltatimes:
            return

        part_time = datetime.strptime(
            time.strftime("%Y/%m/%d")+" "
            +self.get_config(
                self.meeting_type+"hour"), "%Y/%m/%d %H:%M")
        
        i = 0
        for dt in  self.deltatimes:
            end = part_time + timedelta(minutes=dt[0])
            self.deltatimes[i].append(part_time)
            self.deltatimes[i].append(end)
            part_time = end
            i = i + 1

        self.update_parts()

        if len(sings) > 0 and self.sing1 and self.sing1.text == "":
            self.sing1.text = sings[0]
            self.sing1.dispatch("on_text_validate")
        if len(sings) > 1 and self.sing2 and self.sing2.text == "":
            self.sing2.text = sings[1]
            self.sing2.dispatch("on_text_validate")
        if len(sings) > 2 and self.sing3 and self.sing3.text == "":
            self.sing3.text = sings[2]
            self.sing3.dispatch("on_text_validate")
    
    
    def _load_watchtower(self, req, result):
        sings = [""]
        if result:
            wt_parser = KyHtmlParser(result)
            #watchtower_tree = html.fromstring(response)*
            wt_parser.findall_attr({"class": "pubRefs"})\
                .findall_tag("a").findall_tag("strong").gettext()
            wt_songs = wt_parser.parse()
            i = -1
            print "//////////", self.meetingparts
            for wt_song in wt_songs:
                song = wt_song.replace(",", "")
                print "///////", self.meetingparts
                self._insert_part(i, u"[color=#FFA500]05 min : "\
                    +SING_SYMBOL+" "+song+"[/color]")
                sings.append(song)
                self._add_time(5)
                i = i +2
        self._update_program(sings)
    
    def _load_watchtower_error(self, req, result):
        Logger.error(self.name+": Error on _load_watchtower_error: %s", result)
    
    
    def update_parts(self):
        """Update Meeting program with a cursor to show the position"""
        if self.current_part:
            newline = "\n"
        else:
            newline = ""
        self.parts = "[font=data/fonts/"+self.font+"]"+"\n"\
            .join(self.meetingparts[:self.current_part])\
            + newline + RUN_SYMBOL + " "\
            + "\n".join(self.meetingparts[self.current_part:])+"[/font]"
        self.update_time()
    
    def update_time(self, *args):
        """Update timing fo meeting."""
        t = datetime.today()
       # t = datetime.strptime("2016/10/18 19:56", "%Y/%m/%d %H:%M")
        self.time = t.strftime("%H:%M[size=20]%S[/size]")
        return
        
        #### TODO #####
        
        offset_start = (
            t - self.deltatimes[self.current_part][1]).total_seconds()
        offset_end = (
            t - self.deltatimes[self.current_part][2]).total_seconds()
        prepend = ""
        color = "#FFFFFF"
        offset = offset_end
        if offset_start < 0: # Before the part : prepend with +
            offset = -offset_start
            prepend = "-"
            color = "#A7A7A7"
        elif offset_end > 180: # 2 min After the part (Warning)
            color = "#FF0000"
            prepend = WARNING_SYMBOL
        elif offset_end > 0: # After the part
            color = "#FF009D"
            prepend = "! "
        else:
            offset = -offset_end
            color = "#63FF79"
        
        self.offset = "[color="+color+"]"\
            +prepend+strfdelta(int(offset), "%H:%M:%S")
    
    def prev_part(self):
        """Back to previous part."""
        if self.current_part > 0:
            self.current_part = self.current_part - 1
        self.update_parts()

    def next_part(self):
        """Jump to next part."""
        if self.current_part < len(self.deltatimes)-1:
            self.current_part = self.current_part + 1
        self.update_parts()

class MeetingInfosApp(KyApp):
    use_kivy_settings = False
    settings_cls = Settings
    ui = None

    def get_application_config(self):
        return super(MeetingInfosApp, self).get_application_config('ema.ini')
    
    def build(self):
        self.ui = MeetingInfos()
        return self.ui
    
    def on_start(self):
        #print self.get_application_config()
        super(MeetingInfosApp, self).on_start()
        self.ui.congregation =  self.congregation
        self.ui.init()


if __name__ == '__main__':
    shutil.copy("ema.ini", "sdcard/.meetinginfos.ini")
    Window.size = (433, 333)
    MeetingInfosApp().run()
