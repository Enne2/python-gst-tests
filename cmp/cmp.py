import sys, os, time, thread
import gi
gi.require_version('Gst', '1.0')
from gi.repository import Gst, GLib, GObject, Soup
import json

class Source:
    def __init__(self,parent):
        self.parent = parent
        self.videotestsrc = Gst.ElementFactory.make("videotestsrc")
        self.videobox = Gst.ElementFactory.make("videobox")
        self.capsfilter = Gst.ElementFactory.make("capsfilter")
        self.capsfilter.set_property("caps", Gst.Caps.from_string("video/x-raw,width=50,height=50,framerate=25/1"))
        self.videotestsrc.set_state(Gst.State.PLAYING)
        self.capsfilter.set_state(Gst.State.PLAYING)
        self.videobox.set_state(Gst.State.PLAYING)
        self.capsfilter.set_property("caps", Gst.Caps.from_string("video/x-raw,width=50,height=50,framerate=25/1"))


    def transform(self, x, y, z, w, h):
        self.videobox.set_property("top", int(x)*-1)
        self.videobox.set_property("left", int(y)*-1)
        self.capsfilter.set_property("caps", Gst.Caps.from_string("video/x-raw,width="+w+",height="+h+",framerate=25/1"))
        return dict(version='Source transformed')

    def playit(self):
        self.videotestsrc.set_state(Gst.State.PLAYING)
        self.capsfilter.set_state(Gst.State.PLAYING)
        self.videobox.set_state(Gst.State.PLAYING)

    def __del__(self):

        self.videobox.link(self.parent.core_pipeline.get_by_name("vmix"))
        self.parent.core_pipeline.remove(self.capsfilter)
        self.parent.core_pipeline.remove(self.videotestsrc)
        self.parent.core_pipeline.remove(self.videobox)
        self.videotestsrc.set_state(Gst.State.NULL)

        self.capsfilter.set_state(Gst.State.NULL)

        self.videobox.set_state(Gst.State.NULL)


class CmpWall(object):

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
        return dict(version='Source added with id: '+str(id))

    def on_request(self, server, msg, path, query, client, *data):
        #logger.info('on_request %s msg: %s query: %s', path, msg, query)
        #
        ret = {}
        #
        if path == '/':
            ret = dict(version='0.1a')
        elif path.startswith('/add/'):
            id = int(path.replace('/add/', ''))
            ret = self.add_source(id)
        #
        elif path.startswith('/transform/'):
            id = int(path.replace('/transform/', ''))
            print(query)
            #
            ret = self.sources[id].transform(query["x"],query["y"],query["z"],query["w"],query["h"])
        #
        elif path.startswith('/remove/'):
            id = int(path.replace('/remove/', ''))
            #
            del self.sources[id]
            ret = dict(confirm='Source removed')
        else:
            ret = dict(error='not found')
        #
        if ret.get('error'):
            msg.set_status(404)
        else:
            msg.set_status(200)
        msg.set_response('application/json', Soup.MemoryUse.COPY, json.dumps(ret).encode())

    def __init__(self):
        #
        self.server = Soup.Server()
        #
        self.server.add_handler('/', self.on_request)
        self.server.listen_all(8080, Soup.ServerListenOptions.IPV4_ONLY)
        self.server.run_async()
        #pipeline generation
        self.core_pipeline = Gst.parse_launch("videotestsrc name=videotestsrc is-live=true pattern=black do-timestamp=true ! \
        capsfilter name=core_caps caps=video/x-raw,width=1024,height=768,framerate=25/1 ! timeoverlay ! \
        queue name=queuev max-size-buffers=1 \
        max-size-time=0 max-size-bytes=0 silent=1 leaky=2 ! videomixer name=vmix ! videoconvert ! autovideosink")

        self.core_pipeline.set_state(Gst.State.PLAYING)



Gst.init(None)
mainclass = CmpWall()
loop = GLib.MainLoop()
loop.run()
