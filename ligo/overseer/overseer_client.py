# -*- coding: utf-8 -*-
# Copyright (C) Branson Stephens (2015)
#
# This file is part of lvalert-overseer
#
# lvalert-overseer is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# It is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with lvalert-overseer.  If not, see <http://www.gnu.org/licenses/>.

from twisted.internet import reactor, protocol
from twisted.internet.error import ReactorNotRunning, ReactorAlreadyRunning
import json
import threading

class OverseerClient(protocol.Protocol):
    
    def connectionMade(self):
        """
        As soon as a connection is made, send our message.
        """
        self.transport.write(self.factory.message)
    
    def dataReceived(self, data):
        """
        Log the server response appropriately.
        """
        try:
            # First clean out the dictionary. Being careful not to re-assign
            for key in self.factory.rdict.keys():
                self.factory.rdict.pop(key)
            self.factory.rdict.update(json.loads(data))
        except ValueError:
            msg = "server response not JSON: %s" % data
            self.factory.logger.error(msg)
            return
            
        if self.factory.rdict.get('success', None): 
            msg = "transmission succeeded."
            self.factory.logger.debug(msg)
        else:
            errorMsg = self.factory.rdict.get('error', 'No reason given.')
            msg = "transmission failed: %s" % errorMsg
            self.factory.logger.error(msg)
        self.transport.loseConnection()

class OverseerClientFactory(protocol.ClientFactory):
    protocol = OverseerClient

    def __init__(self, message, rdict, logger, standalone):
        self.message = message
        self.logger = logger
        self.standalone = standalone
        self.rdict = rdict

    def clientConnectionFailed(self, connector, reason):
        if self.standalone:
            try:
                reactor.stop()
            except ReactorNotRunning:
                pass
    
    def clientConnectionLost(self, connector, reason):
        if self.standalone:
            try:
                reactor.stop()
            except ReactorNotRunning:
                pass

# Send a dictionary of information to the Overseer
def send_to_overseer(mdict, rdict, logger, standalone=True, port=8000):
    f = OverseerClientFactory(json.dumps(mdict), rdict, logger, standalone)
    if standalone:
        reactor.connectTCP("localhost", port, f)
        # The installSignalHandlers=0 is necessary to avoid a huge volume
        # of warning messages. mod_wsgi doesn't allow these signal handlers
        # to be installed by default anyway, as they could interfere with 
        # Apache sending and receiving signals.
        reactor.run(installSignalHandlers=0)
    else:
        reactor.callFromThread(reactor.connectTCP, "localhost", port, f)


