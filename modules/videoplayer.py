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
kivy.require('1.9.0')

from kivy.app import App
from kivy.uix.video import Video
from kivy.support import install_twisted_reactor
install_twisted_reactor()

from twisted.internet import reactor, protocol

class MyApp(App):
    
    def build(self):
        video = Video(source='/home/ulu/Vidéos/pk_F_014_r720P.mp4')
        video.state='play'
        video.allow_stretch=True
        
        self.connect_to_server()
        return video

    def connect_to_server(self):
        reactor.connectTCP('localhost', 2414, EchoFactory(self))

    def on_connection(self, connection):
        self.print_message("connected successfully!")
        self.connection = connection

if __name__ == '__main__':
    MyApp().run()


class EchoClient(protocol.Protocol):
    def connectionMade(self):
        self.factory.app.on_connection(self.transport)

    def dataReceived(self, data):
        self.factory.app.print_message(data)


class EchoFactory(protocol.ClientFactory):
    protocol = EchoClient

    def __init__(self, app):
        self.app = app

    def clientConnectionLost(self, conn, reason):
        self.app.print_message("connection lost")

    def clientConnectionFailed(self, conn, reason):
        self.app.print_message("connection failed")
