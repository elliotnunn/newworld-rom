# Ripped from somewhere else.
# Can kind-of rip parcels.
# Needs neatening up.

import struct
from binascii import crc32
import lzss
import struct

class ParcelsArea:
    MAGIC = b'prcl \x01\x00\x00\x00 \x00\x00\x00\x14 \x00\x00\x00\x14 \x00\x00\x00\x00'.replace(b' ', b'')
    
    def __init__(self, bytes=None):
        if bytes is not None:
            if not bytes.startswith(self.MAGIC):
                raise ValueError('Instead of a prcl magic number: %r' % bytes[:len(self.MAGIC)])
            
            # Read all the structs in the prcl area!
            prcls = ParcelStruct.scan(bytes=bytes, first_offset=len(self.MAGIC))
            prcls = list(prcls)
            self.prcls = prcls

            for prcl in prcls:
                for entry in prcl.entries:
                    tpl = (entry.load_offset, entry.load_len, entry.compress)

                    x = bytes[entry.load_offset : entry.load_offset+entry.load_len]
                    if entry.compress:
                        x = lzss.extract(x)
                    entry.bytes = x
        
        else:
            self.prcls = []
    
    def __bytes__(self):
        binaries_added = {} # (bytes, compress): (compressed_bytes, offset, cksum)
        things = bytearray(self.MAGIC)

        for prcl in self.prcls:
            prcl_offset = len(things)
            things.extend(bytes(len(prcl)))

            for entry in prcl.entries:
                dict_lookup = (entry.bytes, entry.compress)

                try:
                    if not entry.backref_allowed: raise ValueError
                    final_bytes, bytes_offset, cksum = binaries_added[dict_lookup]
                
                except:
                    # Need to use this binary!
                    final_bytes = entry.bytes
                    if entry.compress:
                        final_bytes = lzss.compress(final_bytes)
                    
                    bytes_offset = len(things)
                    cksum = crc32(final_bytes)

                    things.extend(final_bytes)

                    binaries_added[dict_lookup] = final_bytes, bytes_offset, cksum

                    # Pad to 4-byte boundary. Apple's build tool left pad bytes uninitialised!
                    while len(things) % 4:
                        things.append(0x99)
                
                # Tell this structure where it can find its binary data.
                entry.uncompressed_len = len(entry.bytes)
                entry.save_cksum = cksum if entry.should_checksum else 0
                entry.save_offset = bytes_offset
                entry.save_len = len(final_bytes)
            
            # Then tell it where it can find the next one, if any
            if prcl is self.prcls[-1]:
                prcl.save_nextoffset = 0
            else:
                prcl.save_nextoffset = len(things)

            things[prcl_offset:prcl_offset+len(prcl)] = bytes(prcl)
        
        # So now all structs and all data are placed. Phew.
        return bytes(things)


class ParcelStruct:
    HEADER_FMT = '>I4s4I32s32s'
    
    @classmethod
    def scan(cls, bytes, first_offset):
        offset = first_offset

        while offset:
            parcel = cls(bytes=bytes, offset=offset)
            yield parcel
            offset = parcel.load_nextoffset
    
    def __init__(self, bytes=None, offset=None):
        if bytes is not None:
            load_nextoffset, fourcc, my_len, flags, entry_count, entry_len, name, compat = struct.unpack_from(self.HEADER_FMT, bytes, offset)

            # Checks
            # if entry_len != ParcelEntry.__len__():
            #     raise ValueError('Parcel entry of %d bytes, expected %d' % (entry_len, ParcelEntry.__len__()))
            
            # if my_len != header_size + entry_count*entry_len:
            #     raise ValueError('Incorrect parcel header size field %d not %d' % (my_len, struct.calcsize(self.HEADER_FMT) + entry_count*entry_len))
            
            # Semantics
            self.fourcc = fourcc
            self.name = name.rstrip(b'\0').decode('ascii')
            self.compat = compat.rstrip(b'\0').decode('ascii')
            self.flags = flags

            len_of_entries = entry_count*entry_len
            entry_offsets = range(offset + my_len - len_of_entries, offset + my_len, entry_len)
            self.entries = [ParcelEntry(bytes[o : o+entry_len]) for o in entry_offsets]

            # Ephemerides
            self.load_nextoffset = load_nextoffset
        
        else:
            self.fourcc = b'    '
            self.name = ''
            self.compat = ''
            self.flags = 0

            self.entries = []
    
    def __len__(self):
        return struct.calcsize(self.HEADER_FMT) + sum(len(e) for e in self.entries)
    
    def __bytes__(self):
        save_nextoffset = self.save_nextoffset
        fourcc = self.fourcc
        my_len = len(self)
        flags = self.flags
        entry_count = len(self.entries)
        entry_len = ParcelEntry.__len__()
        name = self.name.encode('ascii')
        compat = self.compat.encode('ascii')

        header = struct.pack(self.HEADER_FMT, save_nextoffset, fourcc, my_len, flags, entry_count, entry_len, name, compat)

        entries = b''.join(bytes(e) for e in self.entries)

        return header + entries

class ParcelEntry:
    FMT = '>4sI4s4I32s'

    def __init__(self, bytes=None):
        if bytes is not None:
            (fourcc, flags, compress, uncompressed_len, load_cksum, load_len, load_offset, name) = struct.unpack(self.FMT, bytes)

            self.fourcc = fourcc
            self.flags = flags
            self.compress = (compress == b'lzss')
            self.uncompressed_len = uncompressed_len
            self.name = name.rstrip(b'\0').decode('ascii')
            self.backref_allowed = False
            self.should_checksum = True

            # Ephemeral stuff
            self.load_cksum = load_cksum
            self.load_len = load_len
            self.load_offset = load_offset
        
        #else:
            # self.fourcc = b'    '
            # self.flags = 0
            # self.compress = False
            # self.uncompressed_len = 0
            # self.name = ''

    def __bytes__(self):
        fourcc = self.fourcc
        flags = self.flags
        compress = b'lzss' if self.compress else b'\0\0\0\0'
        uncompressed_len = self.uncompressed_len
        save_cksum = self.save_cksum
        save_len = self.save_len
        save_offset = self.save_offset
        name = self.name.encode('ascii')

        return struct.pack(self.FMT, fourcc, flags, compress, uncompressed_len, save_cksum, save_len, save_offset, name)
    
    @classmethod
    def __len__(cls):
        return struct.calcsize(cls.FMT)
