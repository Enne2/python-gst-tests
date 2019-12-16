
#!/usr/bin/env python

import sys, os, time, thread
import gi
gi.require_version('Gst', '1.0')
from gi.repository import Gst, GLib, GObject

class CLI_Main(object):

    def __init__(self):
        self.player = Gst.Pipeline.new("player")
        source = Gst.ElementFactory.make("filesrc", "file-source")
        parser = Gst.ElementFactory.make("mpegaudioparse", "parser")
        decoder = Gst.ElementFactory.make("mpg123audiodec", "decoder")
        conv = Gst.ElementFactory.make("audioconvert", "converter")
        sink = Gst.ElementFactory.make("alsasink", "alsa-output")
        source.set_property("location", "test.mp3")
        self.player.add(source)
        self.player.add(parser)
        self.player.add(decoder)
        self.player.add(conv)
        self.player.add(sink)
        source.link(parser)
        parser.link(decoder)
        decoder.link(conv)
        conv.link(sink)

        bus = self.player.get_bus()
        bus.add_signal_watch()
        bus.connect("message", self.on_message)
        self.player.set_state(Gst.State.PLAYING)

    def on_message(self, bus, message):
        t = message.type
        if t == Gst.MessageType.EOS:
            self.player.set_state(Gst.State.NULL)
            self.playmode = False
        elif t == Gst.MessageType.ERROR:
            self.player.set_state(Gst.State.NULL)
            err, debug = message.parse_error()
            print "Error: %s" % err, debug
            self.playmode = False



GObject.threads_init()
Gst.init(None)
mainclass = CLI_Main()
loop = GLib.MainLoop()
loop.run()
