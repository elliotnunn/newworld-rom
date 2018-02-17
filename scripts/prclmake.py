#!/usr/bin/env python3

from prcltool import ParcelsArea, ParcelStruct, ParcelEntry
import argparse
from sys import argv


class DataLoader(argparse.Action):
    def __call__(self, parser, namespace, values, option_string=None):
        path = values[0]

        try:
            p2 = path + '.patch'
            with open(p2, 'rb') as f:
                namespace.bytes = f.read()
            print('Using', p2)
        except FileNotFoundError:
            with open(path, 'rb') as f:
                namespace.bytes = f.read()

class DataReader(argparse.Action):
    def __call__(self, parser, namespace, values, option_string=None):
        d = b''.join(s.encode('ascii')+b'\0' for s in values)
        namespace.bytes = d
        namespace.should_checksum = False

def hex(s):
    return int(s, 16)

def fourcc(s):
    b = s.encode('ascii')
    if len(b) != 4:
        raise ValueError('type code not four bytes')
    return b

p1 = argparse.ArgumentParser()
p2 = argparse.ArgumentParser()

p1.add_argument('--flags', '-f', action='store', type=hex, default=0)
p1.add_argument('--fourcc', '-t', action='store', type=fourcc, default='    ')
p1.add_argument('--name', '-n', action='store', default='')
p1.add_argument('--compat', '-c', action='store', default='')

p2.add_argument('--fourcc', '-t', action='store', type=fourcc, default='    ')
p2.add_argument('--flags', '-f', action='store', type=hex, default=0)
p2.add_argument('--lzss', '-l', action='store_true', dest='compress')
p2.add_argument('--name', '-n', action='store', default='')
p2.add_argument('--backref', action='store_true', dest='backref_allowed')
p2.add_argument('--nosum', action='store_false', dest='should_checksum')
p2.add_argument('--src', '-s', nargs=1, dest='bytes', action=DataLoader)
p2.add_argument('--data', '-d', nargs='+', dest='bytes', action=DataReader)


# Usage: prog.py [ --prcl prcl-opts [ --bin bin-opts ] ... ] ...

progname, dest, *args = argv

groups = []

me = ParcelsArea()

for a in args:
    if a in ('--prcl', '--bin'):
        n = []
        groups.append(n)
    n.append(a)

for g in groups:
    t, *opts = g

    if t == '--prcl':
        prcl = ParcelStruct()
        p1.parse_args(args=opts, namespace=prcl)
        me.prcls.append(prcl)
    elif t == '--bin':
        bn = ParcelEntry()
        p2.parse_args(args=opts, namespace=bn)
        prcl.entries.append(bn)
    else:
        raise ValueError('bad arg')

with open(dest, 'wb') as f:
    f.write(bytes(me))
