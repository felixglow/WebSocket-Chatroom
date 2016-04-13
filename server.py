# -*-coding:utf-8 -*-
#
# Created on 2016-04-13, by felix
#

__author__ = 'felix'

import sys
import random

from twisted.web.static import File
from twisted.python import log
from twisted.web.server import Site
from twisted.internet import reactor

from autobahn.twisted.websocket import WebSocketServerFactory, \
    WebSocketServerProtocol

from autobahn.twisted.resource import WebSocketResource


class ServerProtocol(WebSocketServerProtocol):
    def onOpen(self):
        """连接成功 注册 寻找好友"""
        self.factory.register(self)
        self.factory.find_friend(self)

    def connectionLost(self, reason):
        """断开连接 注销"""
        self.factory.unregister(self)

    def onMessage(self, payload, isBinary):
        """发送消息"""
        self.factory.communicate(self, payload, isBinary)


class RouterFactory(WebSocketServerFactory):
    def __init__(self, *args, **kwargs):
        super(RouterFactory, self).__init__(*args, **kwargs)
        self.clients = {}

    def register(self, client):
        """用户注册"""
        self.clients[client.peer] = {"object": client, "friend": None}

    def unregister(self, client):
        """用户注销"""
        del self.clients[client.peer]

    def find_friend(self, client):
        """寻找好友"""

        friend = [c for c in self.clients if c != client.peer and not self.clients[c]["friend"]]
        if not friend:
            client.sendMessage(u"{0} 您暂时还没有好友在线".format(client.peer).encode("utf-8"))
        else:
            friend_choice = random.choice(friend)
            self.clients[friend_choice]["friend"] = client
            self.clients[client.peer]["friend"] = self.clients[friend_choice]["object"]

    def communicate(self, client, payload, isBinary):
        """传输信息"""
        f = self.clients[client.peer]
        if not f["friend"]:
            f["object"].sendMessage(u"请先连接好友。")
        else:
            f["friend"].sendMessage(payload, isBinary)


if __name__ == "__main__":
    log.startLogging(sys.stdout)
    # 默认为index.html
    root = File(".")

    factory = RouterFactory(u"ws://127.0.0.1:8080")
    factory.protocol = ServerProtocol
    resource = WebSocketResource(factory)
    root.putChild(u"ws", resource)

    site = Site(root)
    reactor.listenTCP(8080, site)
    reactor.run()