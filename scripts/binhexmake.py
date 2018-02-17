#!/usr/bin/env python3


import binhex
import argparse
import os.path


def get_file(filename):
    with open(filename, 'rb') as f:
        return f.read()


def fourcc(s):
    b = s.encode('ascii').ljust(4, b' ')
    if len(b) != 4:
        raise ValueError('wrong length')
    return b


parser = argparse.ArgumentParser(
    description = """Blah."""
)

parser.add_argument('--data', action='store', metavar='FILE', help='Data fork')
parser.add_argument('--rsrc', action='store', metavar='FILE', help='Resource fork')
parser.add_argument('--type', action='store', metavar='FOURCC', type=fourcc, default='    ', help='(space-padded) type code')
parser.add_argument('--creator', action='store', metavar='FOURCC', type=fourcc, default='    ', help='(space-padded) creator code')
parser.add_argument('--name', action='store', metavar='FILENAME', default='', help='archived name (taken from DEST by default)')
parser.add_argument('--has-bundle', action='store_true', help='set Finder flag indicating BNDL resource present')
parser.add_argument('dest', metavar='DEST', help='HQX file')

args = parser.parse_args()


# make an auto filename
if args.name:
    name = args.name
else:
    name = os.path.basename(args.dest)

    base, ext = os.path.splitext(name)
    if ext.lower() == '.hqx':
        name = base

assert name

finfo = binhex.FInfo()
finfo.Creator = args.creator
finfo.Type = args.type
finfo.Flags = 0x2000 if args.has_bundle else 0

rsrc_fork, data_fork = (get_file(f) if f else b'' for f in [args.rsrc, args.data])


bh = binhex.BinHex((name, finfo, len(data_fork), len(rsrc_fork)), args.dest)

bh.write(data_fork)
bh.write_rsrc(rsrc_fork)

bh.close()
