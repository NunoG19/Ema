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

import time
import linphone

from kivy.clock import Clock
from kivy.logger import Logger
from kivy.event import EventDispatcher
from kivy.properties import StringProperty


STAR_SYMBOL = u"[font=data/fonts/ema.ttf]\uE808[/font]"
UNSTAR_SYMBOL = u"[font=data/fonts/ema.ttf]\uE807[/font]"

from kyapp import KyApp

class SipAccount(EventDispatcher):
    
    gain = -30.0
    main_call = None
    calls = []
    global_status = StringProperty("")
    call_status = StringProperty("")
    call_when_ready = None
    auto_call_name = ""
        
    def __init__(self, name, server, user, password, call_slots):
        callbacks = {
            'global_state_changed': self.global_state_changed,
            'registration_state_changed': self.registration_state_changed,
            'call_state_changed' :  self.call_state_changed,
        }
        self.name = name
        self.server = server
        self.call_slots = call_slots
        self.core = linphone.Core.new(callbacks, None, None)
        proxy_cfg = self.core.create_proxy_config()
        proxy_cfg.identity_address = self.core.create_address("sip:"+user+"@"+server)
        proxy_cfg.server_addr = "sip:"+server
        proxy_cfg.register_enabled = True
        self.proxy_cfg = proxy_cfg
        self.core.add_proxy_config(proxy_cfg)
        auth_info = linphone.AuthInfo.new(user, None, password, None, None, server)
        self.core.add_auth_info(auth_info)
        self.core.playback_gain_db =  self.gain
        #self.core.mic_gain_db =  -15.0
        

    def _log(self, log):
        Logger.info(log)

    def start(self):
        Clock.schedule_interval(self.run, 0.1)
        #Clock.schedule_interval(self.update_users, 1)
        #Clock.schedule_interval(self.get_ovh_conference_infos, 30)

    def call(self, name, number, is_main=False):
        Logger.info("SIP/"+self.name+": Calling %s" % number)
        if is_main or len(self.calls) < self.call_slots:
            call = self.core.invite(
                "sip:0033"+number[1:]+"@"+self.server)
            if is_main:
                self.main_call = call
                call.user_data = (0, name)
            else:
                self.calls.append(call)
                call.user_data = (len(self.calls), name)
    
    def run(self, *args):
        self.core.iterate()

    def global_state_changed(self, *args):
        self._log(
            "SIP/"+self.name+": GLOBAL - %d) %s" % (args[1], args[2]))

    def registration_state_changed(self, core, call, state, message):
        self._log(
            "SIP/"+self.name+": REGISTER - %s) %s" % (state, message))
        if state == linphone.RegistrationState.Progress:
            self.global_status = "Progress"
        elif state == linphone.RegistrationState.Ok:
            #self.core.terminate_all_calls()
            self.global_status = "Ok"
        elif state == linphone.RegistrationState.Failed:
            self.global_status = "Failed"
    
    def call_state_changed(self, core, call, state, message):
        if call.user_data:
            self._log(
                "SIP/"+self.name+": CALL#%d - %s) %s" \
                    % (call.user_data[0], state, message))
        else:
            self._log(
                "SIP/"+self.name+": CALL - %s) %s" \
                    % (state, message))            
        if message == "LinphoneCallStreamsRunning":
            self.core.add_all_to_conference()
            self.call_status = "Ok:%d" % call.user_data[0]
        elif (state == linphone.CallState.Error
            or
            state == linphone.CallState.End):
                if call.user_data:
                    if call.user_data[0] == 0:
                        print("MAIN LEAVE")
                        self.main_call = None
                        for other_call in self.calls:
                            self.core.leave_conference(other_call)
                    else:
                        print(self.calls, call.user_data[0])
                        del(self.calls[call.user_data[0]-1])
                    self.call_status = "End:%d" % call.user_data[0]
    
    def get_call_quality(self, call):
        infos = ""
        quality = int(call.current_quality)
        infos = infos + STAR_SYMBOL*(quality)\
            +UNSTAR_SYMBOL*(5-quality)
        infos = infos + " " + call.user_data[1]
        return infos

    def quit(self):
        self.core.terminate_all_calls()


class SipTestApp(KyApp):

    def on_start(self):
        sip = SipAccount(
            "OVH", "sip3.ovh.fr", "0033972584491", "FlkoSV9s")
    

if __name__ == '__main__':
    SipTestApp().run()
    
