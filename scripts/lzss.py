import os.path
import subprocess as sp

def _run(arg, input):
    lzbin = os.path.join(os.path.dirname(__file__), 'lzss')
    p = sp.Popen([lzbin, arg], stdin=sp.PIPE, stdout=sp.PIPE, bufsize=0x400000)
    output, stderr = p.communicate(input)
    return output

def compress(data):
    return _run('c', data)

def extract(data):
    return _run('x', data)
