# Copyright (c) Twisted Matrix Laboratories.
# See LICENSE for details.

from twisted.application.reactors import Reactor

default = Reactor(
    'default', 'twisted.internet.default',
    'The best reactor for the current platform.')

select = Reactor(
    'select', 'twisted.internet.selectreactor', 'select(2)-based reactor.')
wx = Reactor(
    'wx', 'twisted.internet.wxreactor', 'wxPython integration reactor.')
gtk = Reactor(
    'gtk', 'twisted.internet.gtkreactor', 'Gtk1 integration reactor.')
gtk2 = Reactor(
    'gtk2', 'twisted.internet.gtk2reactor', 'Gtk2 integration reactor.')
glib2 = Reactor(
    'glib2', 'twisted.internet.glib2reactor',
    'GLib2 event-loop integration reactor.')
glade = Reactor(
    'debug-gui', 'twisted.manhole.gladereactor',
    'Semi-functional debugging/introspection reactor.')
win32er = Reactor(
    'win32', 'twisted.internet.win32eventreactor',
    'Win32 WaitForMultipleObjects-based reactor.')
poll = Reactor(
    'poll', 'twisted.internet.pollreactor', 'poll(2)-based reactor.')
epoll = Reactor(
    'epoll', 'twisted.internet.epollreactor', 'epoll(4)-based reactor.')
cf = Reactor(
    'cf' , 'twisted.internet.cfreactor',
    'CoreFoundation integration reactor.')
kqueue = Reactor(
    'kqueue', 'twisted.internet.kqreactor', 'kqueue(2)-based reactor.')
iocp = Reactor(
    'iocp', 'twisted.internet.iocpreactor',
    'Win32 IO Completion Ports-based reactor.')
