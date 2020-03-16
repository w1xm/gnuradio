#!/usr/bin/python
import sys
import pprint
from rci import client

if len(sys.argv) < 2:
    raise ValueError('missing command')
command = sys.argv[1]

c = client.Client('ws://localhost:8502/api/ws')

args = []
for a in sys.argv[2:]:
    t, v = a[0], a[1:]
    if t == 'f':
        v = float(v)
    elif t == 'b':
        v = bool(int(v))
    elif t == 'i':
        v = int(v)
    args.append(v)

getattr(c, command)(*args)
with c._cv:
    c._cv.wait()
pprint.pprint(c.status)
