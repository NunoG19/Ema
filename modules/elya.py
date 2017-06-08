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
import time
import base64
import urllib2

from kivy.clock import Clock
from kivy.lang import Builder
from kivy.logger import Logger
from kivy.uix.label import Label
from kivy.event import EventDispatcher
from kivy.uix.boxlayout import BoxLayout
from kivy.properties import StringProperty
from kivy.adapters.simplelistadapter import SimpleListAdapter

from libs.kyapp import KyModule
from libs.sip_account import SipAccount
from libs.ovh_account import OvhAccount

class Elya(KyModule):
    kv_directory = "kv"

    pass_bind = False
    status = StringProperty("")
    bullet_status = StringProperty("data/images/bullet_red.png")
    users = StringProperty("")
    total_users = StringProperty(
        "[size=18sp][b][color=ff3333]0[/color][/b][/font]")
    quality = StringProperty("")

    users_list = {}
    sip_account = None
    ovh_account = None
    
    gain = -30.0
    
    callers = {}

    def load_contacts(self):
        contacts = ""
        filename = self.save_path+os.sep+"contacts.txt"
        if os.path.isfile(filename):
            contacts = open(filename, "rb").read().split("\n")
            for contact in contacts:
                if contact:
                    c = contact.split(":")
                    if len(c) == 2:
                        self.callers[c[0].strip()] = c[1].strip().decode("utf-8")


    def save_contacts(self):
        filename = self.save_path+os.sep+"contacts.txt"
        contacts = []
        for num, name in self.callers.items():
            contacts.append(self._clean_number(num)+" : "+name.encode("utf-8"))
        open(filename, "wb").write("\n".join(contacts))
    
    def connect_sip_account(self):
        """Connect sip account and auto_call if need."""
        name = self.get_config("sip", "name")
        server = self.get_config("sip", "server")
        user = self.get_config("sip", "user")
        password = base64.b64decode(
            self.get_config("sip", "password"))
        self.call_when_ready = self.get_config("sip", "call_when_ready")
        slots = self.get_config("sip", "call_slots")
        self.sip_account = SipAccount(
            name, server, user, password, slots)
        self.sip_account.bind(global_status = self.set_sip_status)
        self.sip_account.bind(call_status = self.set_call_status)
        Clock.schedule_once(lambda dt:  self.sip_account.start(), 1)
        Clock.schedule_interval(self.update_calls_status, 1)
        Clock.schedule_interval(lambda dt:
                self.ovh_account.get_conf_infos(
                self._get_conf_infos),
             30)

    
    def connect_ovh_account(self):
        """Connect ovh account to manage conference."""
        endpoint = self.get_config("ovh", "endpoint")
        application_key = base64.b64decode(
            self.get_config("ovh", "application_key"))
        application_secret = base64.b64decode(
            self.get_config("ovh", "application_secret"))
        consumer_key = base64.b64decode(
            self.get_config("ovh", "consumer_key"))
        billing_account = self.get_config("ovh", "billing_account")
        service_name = self.get_config("ovh", "service_name")
        token = self.get_config("ovh", "token")
        
        self.ovh_account = OvhAccount(
            billing_account, service_name, token,
            endpoint, application_key, application_secret, consumer_key)

    def _get_conf_infos(self, request, infos, if_failed=None):
        print(infos)
        if not infos:
            return
            
        #~ if "msg" in infos and infos["msg"]:
            #~ self.users.text = infos["msg"]
            #~ return
        
        self.users_list = []
        if "value" in infos and "Members" in infos["value"]:
            for user in infos["value"]["Members"]:
                if ("Caller-ID-Name" in user
                    and  user["Caller-ID-Name"] == "09 72 58 44 91"):
                        self.users_list.insert(
                            0,
                            u"PC Salle")
                else:
                    self.users_list.append(
                        self.get_caller_name(user["Caller-ID-Name"]))

    def compose_number(self, *args):
        self.reset_message_event = None
        self.popup = popup = Builder.load_file('kv/phonepad.kv')
        popup.title = "Numéro de téléphone (Fixe seulement)"
        self.select_number = popup.ids["select_number"]
        self.status_message = popup.ids["status_message"]
        self.contact_name = self.popup.ids["contact_name"]
        self.popup.ids["save_contact"].bind(on_press = self.save_contact_name)
        numbers = []
        for number, caller  in self.callers.items():
            numbers.append(self._phonerize(number))
        self.select_number.values = numbers
        self.select_number.bind(text = self._update_name)
        self.select_number._dropdown.bind(
             on_dismiss = lambda x: self._update_name(x, self.select_number.text))
        
        #~ self.select_number._dropdown.bind(
            #~ on_dismiss = self.spinner_to_lightness)
        #~ self.select_number.bind(
            #~ text = lambda obj, text: self.validate_num(text))
        #~ self.popup.background_color = (0, 0, 0, 0)
        #~ self.validate_num(textinput.text)
        for n in range(10):
            b = popup.ids["n"+str(n)]
            b.bind(on_press=self.keynum_pressed)
        b = popup.ids["nDel"]
        b.bind(on_press=self.del_pressed)
        b = popup.ids["nOk"]
        b.text = "Valider"
        b.bind(on_press = self.ok_pressed)
        popup.open()

    def _update_name(self, instance, number):
        num, name = self._get_num_and_name(number)
        self.contact_name.text = name

    def _reset_status_message(self, dt):
         self.status_message.text = ""
        
    def save_contact_name(self, x):
        num, name = self._get_num_and_name(self.select_number.text)
        if len(num) != 15:
            self.status_message.text = "Numéro de téléphone invalide"
            if self.reset_message_event:
                Clock.unschedule(self.reset_message_event)
            self.reset_message_event = Clock.schedule_once(self._reset_status_message, 1)
            return
        name = self.contact_name.text
        if name:
            self.callers[self._clean_number(num)] = name
        elif self._clean_number(num) in self.callers:
            del(self.callers[self._clean_number(num)])
        numbers = []
        for number, caller  in self.callers.items():
            numbers.append(self._phonerize(number))
        self.select_number.values = numbers
        self.save_contacts()
        self.update_phone_number(num+" : "+name)

    def _get_num_and_name(self, number):
        if " : " in number:
            num, name = number.split(" : ")
        else:
            num = number
            name = ""
        return num, name

    def _clean_number(self, number):
        num, name = self._get_num_and_name(number)
        return num.replace(" ", "")

    def _phonerize(self, num):
        """Convert a 0011223344 number to 00 11 22 33 44."""
        num = self._clean_number(num)
        #Be sure number is valid
        try:
            intnum = int(num)
        except:
            print("error")
            intnum = 0
        strnum = "0%d" % intnum
        final = ""
        i = 0
        for c in strnum:
            final = final + c
            i = i + 1
            if i == 2:
                i = 0
                final = final + " "
        return self.get_caller_name(final)
        

    def keynum_pressed(self, button):
        num = self._phonerize(self.select_number.text + button.text)
        print(num)
        if len(num) <= 15 or " : " in num:
            self.update_phone_number(num)

    def del_pressed(self, button):
        num = self._clean_number(self.select_number.text)[:-1]
        print(num)
        self.update_phone_number(num)

    def ok_pressed(self, button):
        self.popup.dismiss()
        number = self.select_number.text
        num, name = self._get_num_and_name(number)
        self.sip_account.call(name, num.replace(" ", ""))

    def get_caller_name(self, caller_id):
        """Return name associated to number"""
        cid = caller_id.replace(" ", "")
        print(self.callers)
        if cid in self.callers:
            self.contact_name.text = self.callers[cid]
            return caller_id+" : "+self.callers[cid]
        else:
            return caller_id

    def update_phone_number(self, number):
        """Update number and contact name"""
        num, name = self._get_num_and_name(number)
        self.select_number.text = self._phonerize(num)
        self.contact_name.text = name
    
    def clean_conference(self):
        """Kick any call from pc"""
        infos = self.ovh_account.get_conf_infos(self._clean_conference)
    
    def _clean_conference(self, request, infos, if_failed=None):
        if infos and "value" in infos:
            if "Members" in infos["value"]:
                for user in infos["value"]["Members"]:
                    print("///////////// Ema here !!!")
                    if user["Caller-ID-Name"] == "09 72 58 44 91":
                        #Kick Ema call from conf
                        self.ovh_account.kick_from_conf(user["ID"])
    
    def set_sip_status(self, obj, status):
        """Set the image of bullet for status of sip connection."""
        if status == "Ok":
            self.bullet_status = "data/images/bullet_green.png"
            
            self.ovh_account.pre_setup_conference()
            
            if self.call_when_ready:
                self.sip_account.call(
                    u"Pc Salle", self.call_when_ready, True)
        elif status == "Progress":
            self.bullet_status = "data/images/bullet_orange.png"
        elif status == "Failed":
            self.bullet_status = "data/images/bullet_red.png"
    
    def set_call_status(self, obj, status):
        """Set the call status."""
        status, call_id = status.split(":")
        if status == "Ok":
           if call_id == "0":
                #Call is made by Elya to connect pc to conference
                self.ovh_account.post_setup_conference()
                self.ovh_account.get_conf_infos(self._get_conf_infos)
        elif status == "End":
            if call_id == "0":
                #Call made by Elya need be restarted
                self.ovh_account.pre_setup_conference()
                Clock.schedule_once(
                    lambda dt:  self.sip_account.call(
                        u" Pc Salle", self.call_when_ready, True), 1)


    def update_calls_status(self, *args):
        infos = "[color=#FFA500]Appels Emis[/color]\n"
        if self.sip_account.main_call:
            infos = infos + self.sip_account.get_call_quality(
                self.sip_account.main_call)
        for call in self.sip_account.calls:
            infos = infos + "\n" \
                + self.sip_account.get_call_quality(call)
        infos = infos\
            +u"\n[color=#FFA500]Appels en Conférence[/color]\n"\
            +"\n".join(self.users_list)
        self.users = infos
        if self.users_list:
            self.total_users =\
                "[b][color=#FFC300]%d[/color][/b]" \
                    % (len(self.users_list)-1)
        else:
            self.total_users = "[b][color=#FF3200]0[/color][/b]"

    def quit(self):
        """Ask sip account to terminate all calls."""
        self.sip_account.quit()
