import sys, os, time, thread
import gi
gi.require_version('Gst', '1.0')
from gi.repository import Gst, GLib, GObject, Soup
import json

class Source:
    def __init__(self):
        self.videotestsrc = Gst.ElementFactory.make("videotestsrc")
        self.videobox = Gst.ElementFactory.make("videobox")
        self.capsfilter = Gst.ElementFactory.make("capsfilter")
        self.capsfilter.set_property("caps", Gst.Caps.from_string("video/x-raw,width=50,height=50,framerate=25/1"))

    def playit(self):
        self.videotestsrc.set_state(Gst.State.PLAYING)
        self.capsfilter.set_state(Gst.State.PLAYING)
        self.videobox.set_state(Gst.State.PLAYING)
        print("Printed immediately.")
        time.sleep(2.4)
        print("Printed after 2.4 seconds.")
        self.videobox.set_property("top", 0)
        self.capsfilter.set_property("caps", Gst.Caps.from_string("video/x-raw,width=50,height=50,framerate=25/1"))
        for x in range(500):
            print(50+x)
            self.videobox.set_property("top", x*-1)
            self.videobox.set_property("left", x*-1)
            self.capsfilter.set_property("caps", Gst.Caps.from_string("video/x-raw,width="+str(50+x)+",height="+str(50+x)+",framerate=25/1"))
            time.sleep(0.1)

class VideoWall(object):

    sources = {}

    def add_source(self,id):
        #sources = Source()
        self.sources[id]=Source()
        #Add Elements
        self.core_pipeline.add(self.sources[id].videotestsrc)
        self.core_pipeline.add(self.sources[id].capsfilter)
        self.core_pipeline.add(self.sources[id].videobox)
        #Link Elements
        self.sources[id].videotestsrc.link(self.sources[id].capsfilter)
        self.sources[id].capsfilter.link(self.sources[id].videobox)

        self.sources[id].videobox.link(self.core_pipeline.get_by_name("vmix"))
        self.sources[id].playit()


    def __init__(self):
        #
        self.server = Soup.Server()
        def on_request(server, msg, path, query, client, *data):
            #logger.info('on_request %s msg: %s query: %s', path, msg, query)
            #
            ret = {}
            #
            if path == '/':
                ret = dict(version='0.1a')
            elif path.startswith('/add/'):
                id = int(path.replace('/add/', ''))
                self.add_source(id)
                ret = dict(version='shit')
            #
            elif path.startswith('/remove/'):
                id = int(path.replace('/remove/', ''))
                #
                ret = self.remove_publisher(id)
            else:
                ret = dict(error='not found')
            #
            if ret.get('error'):
                msg.set_status(404)
            else:
                msg.set_status(200)
            msg.set_response('application/json', Soup.MemoryUse.COPY, json.dumps(ret).encode())
        #
        self.server.add_handler('/', on_request)
        self.server.listen_all(8080, Soup.ServerListenOptions.IPV4_ONLY)
        self.server.run_async()
        #pipeline generation
        self.core_pipeline = Gst.parse_launch("videotestsrc name=videotestsrc is-live=true pattern=black do-timestamp=true ! \
        capsfilter name=core_caps caps=video/x-raw,width=1024,height=768,framerate=25/1 ! \
        queue name=queuev max-size-buffers=1 \
        max-size-time=0 max-size-bytes=0 silent=1 leaky=2 ! videomixer name=vmix ! videoconvert ! autovideosink")

        self.core_pipeline.set_state(Gst.State.PLAYING)



Gst.init(None)
mainclass = VideoWall()
loop = GLib.MainLoop()
loop.run()
