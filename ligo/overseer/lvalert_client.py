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

#-------------------------------------------------------------------------------------
#-------------------------------------------------------------------------------------
# Utilities for interacting with LVAlert
# These are based on lvalert_listen and lvalert_send by Patrick Brady and Brian Moe.
#-------------------------------------------------------------------------------------
#-------------------------------------------------------------------------------------
import libxml2

# pubsub import must come first because it overloads part of the
# StanzaProcessor class
from ligo.lvalert import pubsub
from pyxmpp.all import JID,TLSSettings
from pyxmpp.jabber.all import Client
from pyxmpp.interface import implements
from pyxmpp.interfaces import IMessageHandlersProvider

from ligo.overseer.overseer_client import send_to_overseer

#-------------------------------------------------------------------------------------
#-------------------------------------------------------------------------------------
# LVAlert message handler for listening client
#-------------------------------------------------------------------------------------
#-------------------------------------------------------------------------------------
class LVAlertMessageHandler(object):
    implements(IMessageHandlersProvider)
   
    def __init__(self, client):
        self.client = client

    def get_message_handlers(self):
        """Return list of (message_type, message_handler) tuples.

        The handlers returned will be called when matching message is received
        in a client session."""
        return [
            (None, self.message),
            ]

    def message(self,stanza):
        message = self.get_entry(stanza)
        node = self.get_node(stanza)
        if message:
            self.client.logger.debug("node=%s message=%s" % (node, message))
            # The LVAlert listening client is meant to be run in a thread by the overseer.
            # So the client created by send_to_overseer is not in standalone mode.
            rdict = {}
            send_to_overseer({'message': message, 'node_name': node, 'action': 'pop'}, 
                rdict, self.client.logger, standalone=False, port=self.client.overseer_port)

            # XXX Should we be doing something with the return dict?
    
        return True

    def get_node(self,stanza):
        c = stanza.xmlnode.children
        c = c.children
        if c:
            return c.prop("node")

    def get_entry(self,stanza):
        c = stanza.xmlnode.children
        while c:
            try:
                if c.name=="event":
                    return c.getContent()
            except libxml2.treeError:
                pass
            c = c.next
        return None

#-------------------------------------------------------------------------------------
#-------------------------------------------------------------------------------------
# LVAlert client class
#-------------------------------------------------------------------------------------
#-------------------------------------------------------------------------------------

class LVAlertClient(Client):
    def __init__(self, jid, password, max_attempts, logger, overseer_port):
        self.jid = jid
        self.max_attempts = max_attempts
        self.logger = logger
        self.overseer_port = overseer_port

        t=TLSSettings(require=True,verify_peer=False)

        Client.__init__(self, self.jid, password, \
            auth_methods=["sasl:GSSAPI","sasl:PLAIN"], tls_settings=t,keepalive=30)

        # add the message handler 
        self.interface_providers = [
            LVAlertMessageHandler(self),
            ]

        # A counter for the onTimeout function
        self.counter = 0

    def stream_state_changed(self,state,arg):
        self.logger.debug("state changed: %s %r " % (state,arg))

    def sendMessage(self,node,msg):
        """Send a message"""
        self.logger.debug("node = %s, message = %s" % (node, msg))
        # In practice, the recipient JID has the same domain part as the login JID.
        recpt = JID("pubsub."+self.jid.domain)
        ps = pubsub.PubSub(from_jid = self.jid, to_jid = recpt, stream = self.stream,
                           stanza_type = "get")
        ps.publish(msg,node)
        self.stream.set_response_handlers(ps,
                self.onSuccess,
                self.onError,
                lambda stanza: self.onTimeout(stanza,node,msg,recpt))
        self.stream.send(ps)

    def onSuccess(self,stanza):
        self.logger.debug("send operation successful ")
        return True

    def onError(self,stanza):
        errorNode = stanza.get_error()
        self.logger.error("error type = %s " % errorNode.get_type())
        self.logger.error("error message = %s " % errorNode.get_message())
        self.logger.info("disconnecting ")
        self.disconnect()
        return True

    def onTimeout(self,stanza,node,msg,recpt):
        self.logger.info("operation timed out.  Trying again... ")
        if self.counter < self.max_attempts:
            self.counter = self.counter + 1
            self.sendMessage(node,msg,recpt)
        else:
            self.logger.error("reached max_attempts. Disconnecting... ")
            self.disconnect()
        return True

