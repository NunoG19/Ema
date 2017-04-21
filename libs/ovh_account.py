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

import ovh
import webbrowser

from kivy.clock import Clock
from kivy.logger import Logger
from kivy.event import EventDispatcher
from kivy.properties import StringProperty

from kyurlrequest import KyUrlRequest

class OvhAccount(EventDispatcher):
    
    OVH_URL = "http://www.ovh.com/cgi-bin/telephony/webconf.pl?token="
    
    def __init__(self, billing_account, service_name, token,
            endpoint, application_key, 
            application_secret, consumer_key):
        self.web_opened = False
        self.req = KyUrlRequest("Ovh/Url")
        self.billing_account = billing_account
        self.service_name = service_name
        self.token = token
        self.ovh_client = ovh.Client(
            endpoint=endpoint,
            application_key=application_key,
            application_secret=application_secret,
            consumer_key=consumer_key,
        )
    
    def _req(self, action):
        return "/telephony/"+self.billing_account\
            +"/conference/"+self.service_name+"/"+action
    
    def open_conference_url(self):
        """Open a browser on conference management webpage."""
        if not self.web_opened:
            webbrowser.open(self.OVH_URL+self.token)
            self.web_opened = True
    
    def get_conf_infos(self, callback):
        """Get informations about conference."""
        self.req.open(
            self.OVH_URL+self.token+"&action",
            callback, lambda *x: self.open_conference_url())
    
    def kick_from_conf(self, uid):
        """Kick user from conference."""
        self.req.open(
            self.OVH_URL+self.token+"&action=kick&memberid=%s" % uid)
    
    def pre_setup_conference(self):
        """Setup conference before main call with enterMute to False."""
        try:
            result = self.ovh_client.put(self._req("settings"), 
                recordStatus=False,
                anonymousRejection=True,
                enterMuted=False,
            )
        except Exception, e:
             Logger.warning(
                "Ovh: Error in pre_setup_conference : %s", e)

    def post_setup_conference(self):
        """Setup conference after main call with enterMute to True."""
        try:
            result = self.ovh_client.put(self._req("settings"), 
                enterMuted=True,
            )
        except Exception, e:
             Logger.warning(
                "Ovh: Error in post_setup_conference : %s", e)









