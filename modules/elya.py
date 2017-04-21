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
    
    callers = {
        "0629221202": u"Frère Nuno Gonçalves",
    }
    
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
        self.popup = popup = Builder.load_file('kv/numpad.kv')
        popup.title = "Numéro de téléphone (Fixe seulement)"
        self.select_number = popup.ids["select_number"]
        self.select_text = self.popup.ids["select_text"]
        numbers = []
        for number, caller  in self.callers.items():
            numbers.append(self._phonerize(number)+" :  "+caller)
        self.select_number.values = numbers
        #~ self.select_number.bind(on_press = self.spinner_to_darkness)
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

    def _clean_number(self, num):
        if ":" in num:
            num = num.split(":")[0]
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
        return final

    def keynum_pressed(self, button):
        num = self._phonerize(self.select_number.text + button.text)
        if len(num) <= 15:
            self.select_number.text = self.get_caller_name(num)
        

    def del_pressed(self, button):
        num = self._phonerize(self.select_number.text)
        if num[-1] != " ":
            self.select_number.text = num[:-1]
        else:
            self.select_number.text = num[:-2]

    def ok_pressed(self, button):
        self.popup.dismiss()
        num = self.select_number.text
        if ":" in num:
            num, name = num.split(":")
        else:
            name = num
        
        self.sip_account.call(name, num.replace(" ", ""))

    def get_caller_name(self, caller_id):
        """Return name associated to number"""

        cid = caller_id.replace(" ", "")
        if cid in self.callers:
            return caller_id+" : "+self.callers[cid]
        else:
            return caller_id
    
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
    
    
    
    
    
    
    
    
    
    #~ def connect_ovh(self):
        #~ # http://www.ovh.com/cgi-bin/telephony/webconf.pl?token=756978792c123dc0b3fc89afe0c866150a83aa36&action
        #~ self.ovh_client = ovh.Client(
            #~ endpoint="ovh-eu",
            #~ application_key="oOVVC9hyUlzO5ws9",
            #~ application_secret="7ijntRlikmr09oTReoZ3yElVHATVM48o",
            #~ consumer_key="D8UJY0WPxdeAZVtbbA9j4ZvROIDCpEVZ",
        #~ )
        
    #~ def get_ovh_filled_request(self, request):
        #~ return request.replace("{billingAccount}", "gj248003-ovh-1").replace("{serviceName}", "0033972584648")

    #~ def pre_setup_ovh_conference(self):
        #~ try:
            #~ result = self.ovh_client.put(self.get_ovh_filled_request("/telephony/{billingAccount}/conference/{serviceName}/settings"), 
                #~ recordStatus=False,
                #~ anonymousRejection=True,
                #~ enterMuted=False,
            #~ )
        #~ except Exception, e:
             #~ Logger.warning("Elya: Erreur dans pre_setup_ovh_conference : %s", e)
        
    #~ def setup_ovh_conference(self):
        #~ try:
            #~ result = self.ovh_client.put(self.get_ovh_filled_request("/telephony/{billingAccount}/conference/{serviceName}/settings"), 
                #~ enterMuted=True,
            #~ )
        #~ except:
            #~ return
        #~ print "SETUP:",json.dumps(result, indent=4)

    #~ def kick_from_ovh_conference(self, uid):
        #~ try:
            #~ response = urllib2.urlopen(
                #~ "http://www.ovh.com/cgi-bin/telephony/webconf.pl?token=756978792c123dc0b3fc89afe0c866150a83aa36&action=kick&memberid=%s" % uid,
                #~ timeout=3).read(10000)
        #~ except Exception, e:
             #~ Logger.warning("Elya: Erreur dans _get_ovh_conference_infos : %s", e)
        #~ return
        
        
        #~ try:
            #~ result = self.ovh_client.post(self.get_ovh_filled_request("/telephony/{billingAccount}/conference/{serviceName}/participants/"+uid+"/kick"))
        #~ except Exception, e:
            #~ Logger.warning("Elya: Erreur dans kick_from_ovh_conference : %s", e)
            #~ return
        #~ print "KICK:",json.dumps(result, indent=4)

    #~ def _get_ovh_conference_infos(self):
        #~ try:
            #~ response = urllib2.urlopen(
                #~ "http://www.ovh.com/cgi-bin/telephony/webconf.pl?token=756978792c123dc0b3fc89afe0c866150a83aa36&action",
                #~ timeout=3).read(10000)
        #~ except Exception, e:
            #~ Logger.warning("Elya: Erreur dans _get_ovh_conference_infos : %s", e)
            #~ return False
        
        #~ infos = json.loads(response)
        #~ print infos
        #~ return infos
    
    #~ def get_caller_name(self, caller_id):
        #~ callers = {
            #~ "0629221202": u"Frère Nuno Gonçalves",
        #~ }
        #~ cid = caller_id.replace(" ", "")
        #~ if cid in callers:
            #~ return caller_id+" : "+callers[cid]
        #~ else:
            #~ return caller_id
    
    #~ def get_ovh_conference_infos(self, *args):
        #~ infos = self._get_ovh_conference_infos()
        #~ time.sleep(3)
        #~ if not infos:
            #~ return
            
        #~ if infos["msg"]:
            #~ self.users.text = infos["msg"]
            #~ return
        
        #~ self.users_list = []
        #~ if "Members" in infos["value"]:
            #~ for user in infos["value"]["Members"]:
                #~ if user["Caller-ID-Name"] == "09 72 58 44 91":
                    #~ self.users_list.insert(
                        #~ 0,
                        #~ u"PC Salle")
                #~ else:
                    #~ self.users_list.append(
                        #~ self.get_caller_name(user["Caller-ID-Name"]))

    #~ def connect(self, *args):
        #~ self.connect_ovh()
        #~ infos = self._get_ovh_conference_infos()
        #~ if infos:
            #~ if "Members" in infos["value"]:
                #~ for user in infos["value"]["Members"]:
                    #~ print "///////////// Ema here !!!"
                    #~ if user["Caller-ID-Name"] == "09 72 58 44 91":
                        #~ #Kick Ema from conf
                        #~ self.kick_from_ovh_conference(user["ID"])
                        
            #~ Logger.info("OVH: "+str(infos))

        #~ self.pre_setup_ovh_conference()
        #~ #self.users.adapter = SimpleListAdapter(data=[], cls=Label)
        #~ callbacks = {
            #~ 'global_state_changed': self.global_state_changed,
            #~ 'registration_state_changed': self.registration_state_changed,
            #~ 'call_state_changed' :  self.call_state_changed,
        #~ }
        #~ self.core = linphone.Core.new(callbacks, None, None)
        #~ proxy_cfg = self.core.create_proxy_config()
        #~ proxy_cfg.identity_address = self.core.create_address("sip:0033972584491@sip3.ovh.fr")
        #~ proxy_cfg.server_addr = "sip:sip3.ovh.fr"
        #~ proxy_cfg.register_enabled = True
        #~ self.proxy_cfg = proxy_cfg
        #~ self.core.add_proxy_config(proxy_cfg)
        #~ auth_info = linphone.AuthInfo.new("0033972584491", None, "FlkoSV9s", None, None, "sip3.ovh.fr")
        #~ self.core.add_auth_info(auth_info)
        #~ self.core.playback_gain_db =  self.gain
        #~ Clock.schedule_once(lambda dt:  self.start(), 1)
       

    #~ def global_state_changed(self, *args):
        #~ self.log("Elya/Global: %d) %s" % (args[1], args[2]))

    #~ def _call(self):
        #~ if self.core.calls_nb == 0:
            #~ self.call = self.core.invite(
                #~ "sip:0033972584648@sip3.ovh.fr")
            #~ self.call.user_data = u"PC Salle"

    #~ def registration_state_changed(self, core, call, state, message):
        #~ self.log("Elya/Regist.: %s) %s" % (state, message))
        #~ if state == linphone.RegistrationState.Progress:
            #~ self.set_bullet_status("progress")
        #~ elif state == linphone.RegistrationState.Ok:
            #~ self.core.terminate_all_calls()
            #~ self.set_bullet_status("ok")
            #~ self._call()
            #~ Clock.schedule_once(lambda dt:  self._call(), 10)
        #~ elif state == linphone.RegistrationState.Failed:
            #~ self.set_bullet_status("ko")
    
    #~ def call_state_changed(self, core, call, state, message):
        #~ self.log(
            #~ "Elya/Call: %s) %s" % (state, message))
        #~ if message == "LinphoneCallStreamsRunning":
            #~ self.get_ovh_conference_infos()
            #~ self.setup_ovh_conference()
        #~ elif self.do_recall and (state == linphone.CallState.Error
            #~ or
            #~ state == linphone.CallState.End):
                #~ self.quit()
                #~ self.pre_setup_ovh_conference()
                #~ Clock.schedule_once(lambda dt:  self._call(), 1)

    #~ def set_bullet_status(self, status):
        #~ if status == "ok":
            #~ self.bullet_status = "data/images/bullet_green.png"
        #~ elif status == "progress":
            #~ self.bullet_status = "data/images/bullet_orange.png"
        #~ elif status == "ko":
            #~ self.bullet_status = "data/images/bullet_red.png"

    #~ def set_total_users(self, total):
        #~ if total:
            #~ self.total_users =\
                #~ "[b][color=#FFC300]%d[/color][/b]" % (total-1)
        #~ else:
            #~ self.total_users = "[b][color=#FF3200]0[/color][/b]"

    #~ def start(self):
        #~ Clock.schedule_interval(self.run, 0.1)
        #~ Clock.schedule_interval(self.update_users, 1)
        #~ Clock.schedule_interval(self.get_ovh_conference_infos, 30)
    
    #~ def run(self, *args):
        #~ self.core.iterate()
        
    #~ def quit(self):
        #~ self.do_recall = False
        #~ self.core.terminate_all_calls()


    #~ def update_users(self, *args):
        #~ if self.call:
            #~ quality = int(self.call.current_quality)
            #~ stars = STAR_SYMBOL*(quality)+UNSTAR_SYMBOL*(5-quality)
            #~ stars = stars + " "+self.call.user_data+"\n"
        #~ else:
            #~ stars = ""
        
        #~ self.users = "[color=#FFA500]Appels Emis[/color]\n"+stars\
            #~ +u"\n[color=#FFA500]Appels en Conférence[/color]\n"\
            #~ +"\n".join(self.users_list)
        #~ self.set_total_users(len(self.users_list))




























    #~ def get_ovh_conference_infos(self, *args):
        #~ try:
            #~ result = self.ovh_client.get(self.get_ovh_filled_request("/telephony/{billingAccount}/conference/{serviceName}/participants"))
        #~ except:
            #~ print "Nobody"
        #~ else:
            #~ changes = False
            #~ users = []
            #~ if result:
                #~ for user in result:
                    #~ user = str(user)
                    #~ print "???", user, self.users_list
                    #~ if not user in self.users_list:
                        #~ changes = True
                        #~ result = self.ovh_client.get(self.get_ovh_filled_request("/telephony/{billingAccount}/conference/{serviceName}/participants/"+user))
                        #~ print result
                        #~ self.users_list[user] = result["callerNumber"]
                    #~ users.append(user)
                
                #~ for user in self.users_list.copy():
                    #~ if not user in users:
                        #~ changes = True
                        #~ del(self.users_list[user])
                
                #~ if changes:
                    #~ self.update_users()

    #~ def link(self, key, obj):
        #~ if not key in self.links:
            #~ self.links[key] = []
        #~ self.links[key].append(obj)
        
    #~ def call(self, key, value):
        #~ if key in self.links:
            #~ for obj in self.links[key]:
                #~ print "call:", obj, value
                #~ obj(value)
    
    #~ def global_state_changed(self, *args, **kwargs):
        #~ self.log("global_state_changed: %r %r" % (args, kwargs))

    #~ def registration_state_changed(self, core, call, state, message):
        #~ print "ici"
        
        #~ self.log("registration_state_changed: " + str(state) + ": " + message)
        
        #~ if state == linphone.RegistrationState.Progress:
            #~ self.set_status("progress")
        #~ elif state == linphone.RegistrationState.Ok:
            #~ self.set_status("ok")
            #~ self.log("call_state_changed: " + self.proxy_cfg.normalize_phone_number("+33972584648")+"----"+str(self.core.invite("sip:0033972584648@sip3.ovh.fr")))
        #~ elif state == linphone.RegistrationState.Failed:
            #~ self.set_status("ko")

    #~ def call_state_changed(self, core, call, state, message):
        #~ user = call.remote_address.as_string_uri_only()
        #~ suser = user.split("@")
        #~ if suser[1] == "freephonie.net":
            #~ user = suser[0][4:]
            
        #~ if state == linphone.CallState.IncomingReceived:
        #~ ### INCOMING CALL
            #~ params = core.create_call_params(call)
            #~ #params.audio_direction = linphone.MediaDirection.RecvOnly
            #~ self.core.accept_call_with_params(call, params)
            #~ self.core.add_to_conference(call)
            #~ self.add_user(user)
            #~ self.calls[user] = call
        #~ elif state == linphone.CallState.End or state == linphone.CallState.Error or state == linphone.CallState.Released:
        #~ ### END OF CALL
            #~ self.remove_user(user)
            #~ if user in self.calls:
                #~ del(self.calls[user])

        #~ self.log("call_state_changed: " + str(state) + ": " + message)


    #~ def log_handler(self, level, msg):
        #~ method = getattr(logging, level)
        #~ method(msg)

    #~ def decode(self, string):
        #~ d = base64.b64decode(string)
        #~ final = ""
        #~ i = 1
        #~ for c in d:
            #~ if i % 2:
                #~ final = final + c
            #~ i = i + 1
        #~ return final

    #~ def set_total_users(self, total):
        #~ if total:
            #~ self.total_users.text = "[b][color=#FFC300]%d[/color][/b]" % total
        #~ else:
            #~ self.total_users.text = "[b][color=#FF3200]0[/color][/b]"

    #~ def add_user(self, user):
        #~ self.users_list[user] = user
        #~ self.users.text = "\n".join(self.users_list.keys())
        #~ self.set_total_users(len(self.users_list.keys()))
        
    #~ def remove_user(self, user):
        #~ if user in self.users_list:
            #~ del(self.users_list[user])
            #~ self.users.text = "\n".join(self.users_list.keys())
            #~ self.set_total_users(len(self.users_list.keys()))
    
    
    #~ def switch_mute(self):
        #~ self.gain = -30 - self.gain
        #~ self.core.playback_gain_db = self.gain
