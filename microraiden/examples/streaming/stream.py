import json
import gevent
from gevent import Greenlet
from gevent.queue import Queue
import sys


class Server:

    def __init__(self, path, offset=0):
        self._frames = []
        self.load_stream(path, offset)

    def load_stream(self, path, offset):
        stream_data = json.load(open(path))
        print(offset, type(offset))
        self._frames = stream_data['stdout'][offset:]

    @property
    def num_frames(self):
        return len(self._frames)

    def get_frame(self, num):
        delay, data = self._frames[num % self.num_frames]
        return delay, data


class Buffer(Greenlet):
    latency = 0.01

    def __init__(self, server, num_frames=1000):
        self.server = server
        self.num_frames = num_frames
        self.frames = Queue(100)
        Greenlet.__init__(self)

    def _run(self):
        for i in range(self.num_frames):
            # request data
            # print('sleep')
            gevent.sleep(self.latency)
            # print('get')
            f = self.server.get_frame(i)
            # print('pre put')
            self.frames.put(f)  # blocks if full
            # print('post put')

    def get_frame(self):
        return self.frames.get()  # blocks if empty


class Client:

    def __init__(self, _buffer):
        self.buffer = _buffer

    def play_stream(self, speed=1.):
        for i in range(self.buffer.num_frames):
            # print('b_get')
            delay, data = self.buffer.get_frame()
            # print('post_get')
            delay /= speed
            self.render(delay, data)

    def render(self, delay, data):
        gevent.sleep(delay)
        msg = '\nbuffer len:{}'.format(len(self.buffer.frames))
        print(data + msg)
        sys.stdout.flush()


def main():
    parrot_json = 'asciicast-113643.json'
    s = Server(path=parrot_json, offset=19)
    b = Buffer(s, num_frames=1000)
    b.start()
    c = Client(b)
    c.play_stream(2)
    b.join()


if __name__ == '__main__':
    main()
