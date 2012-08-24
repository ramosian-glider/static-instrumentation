#!/usr/bin/env python
from disasm import disassembler
from macho_defs import *
import os
import struct
import sys


class MachOError(Exception):
  """A class for exceptions thrown by this module."""
  pass


def CheckedSeek(file, offset):
  """Seeks the file-like object at |file| to offset |offset| and raises a
  MachOError if anything funny happens."""

  file.seek(offset, os.SEEK_SET)
  new_offset = file.tell()
  if new_offset != offset:
    raise MachOError, \
          'seek: expected offset %d, observed %d' % (offset, new_offset)


def CheckedRead(file, count):
  """Reads |count| bytes from the file-like |file| object, raising a
  MachOError if any other number of bytes is read."""

  bytes = file.read(count)
  if len(bytes) != count:
    raise MachOError, \
          'read: expected length %d, observed %d' % (count, len(bytes))
  return bytes

def CheckedWrite(file, bytes):
  """Actually not checked."""
  file.write(bytes)

def ReadUInt32(file, endian):
  """Reads an unsinged 32-bit integer from the file-like |file| object,
  treating it as having endianness specified by |endian| (per the |struct|
  module), and returns it as a number. Raises a MachOError if the proper
  length of data can't be read from |file|."""

  bytes = CheckedRead(file, 4)

  (uint32,) = struct.unpack(endian + 'I', bytes)
  return uint32

class MachOBase(object):
  def __init__(self, offset):
    self._file_size = 0
    self._file_offset = offset
  def write_to_file(self, file_stream):
    raise MachOError, "Unimplemented write_to_file in MachOBase"

# For all the MachO classes the offset must be valid, i.e. the classes
# may potentially seek to it.
class MachOHeader(MachOBase):
  def __init__(self, file, offset=0):
    super(MachOHeader, self).__init__(offset)
    CheckedSeek(file, offset)
    magic = ReadUInt32(file, '<')
    if magic == MH_MAGIC or magic == MH_MAGIC_64:
      self.endian = '<'
    elif magic == MH_CIGAM or magic == MH_CIGAM_64:
      self.endian = '>'
    else:
      raise MachOError, \
          'Mach-O file at offset %d has illusion of magic: %x' % (offset, magic)
    if magic in [MH_MAGIC_64, MH_CIGAM_64]:
      self.bits = 64
      self._file_size = 32
    else:
      self.bits = 32
      self._file_size = 28
    CheckedSeek(file, offset)
    bytes = CheckedRead(file, 28)
    (self.magic, self.cputype, self.cpusubtype,
     self.filetype, self.ncmds, self.sizeofcmds,
     self.flags) = struct.unpack(self.endian + '7I', bytes)
    if self.bits == 64:
      self.reserved = ReadUInt32(file, self.endian)
  # TODO(glider): write_to_buf
  def write_to_file(self, file_stream):
    CheckedSeek(file_stream, self._file_offset)
    bytes = struct.pack(self.endian + '7I', self.magic,
                        self.cputype, self.cpusubtype, self.filetype,
                        self.ncmds, self.sizeofcmds, self.flags)
    CheckedWrite(file_stream, bytes)
    if self.bits == 64:
      bytes = struct.pack(self.endian + '1I', self.reserved)
      CheckedWrite(file_stream, bytes)

def MachOLoadCommandFactory(endian, bits, file, offset):
  # TODO(glider): this is suboptimal: an extra scan.
  lc0 = MachOLoadCommand(endian, bits, file, offset)
  if (lc0.cmd, bits) in [(LC_SEGMENT, 32), (LC_SEGMENT_64, 64)]:
    return MachOSegmentCommand(endian, bits, file, offset)
  # Fallthrough.
  return lc0

def MachOSectionFactory(endian, bits, file, offset):
  sect0 = MachOSection(endian, bits, file, offset)
  if sect0.sectname.startswith('__text\x00'):
    return MachOTextSection(endian, bits, file, offset)
  # Fallthrough.
  return sect0

class MachOLoadCommand(MachOBase):
  def __init__(self, endian, bits, file, offset=0):
    super(MachOLoadCommand, self).__init__(offset)
    CheckedSeek(file, offset)
    self.cmd = ReadUInt32(file, endian)
    self.cmdsize = ReadUInt32(file, endian)
    self._file_size = self.cmdsize
  # static
  def cmd_str(self):
    prefix = LoadCmdToStr(self.cmd)
    return '%s: %s' % (prefix, hex(self.cmd))
  def __str__(self):
    result = "%s of %d bytes:\t%s" % (
      self.__class__.__name__, self._file_size, MachOLoadCommand.cmd_str(self))
    return result
  def write_to_file(self, endian, file_stream, offset):
    CheckedSeek(file_stream, offset)
    WriteUInt32(file, endian, self.cmd)
    WriteUInt32(file, endian, self.cmdsize)

# vm_prot_t is int, essentially.
class MachOSegmentCommand(MachOLoadCommand):
  def __init__(self, endian, bits, file, offset):
    super(MachOSegmentCommand, self).__init__(endian, bits, file, offset)
    offset += 8  # 8 bytes already read by the parent ctor
    CheckedSeek(file, offset)
    if bits == 64:
      bytes = CheckedRead(file, 64)
      (self.segname, self.vmaddr, self.vmsize,
       self.fileoff, self.filesize, self.maxprot, self.initprot,
       self.nsects, self.flags) = struct.unpack(endian + '16s4Q2i2I', bytes)
      offset += 64
    else:
      raise MachOError, 'LC_SEGMENT not implemented'
    self.sections = []
    for i in range(self.nsects):
      sect = MachOSectionFactory(endian, bits, file, offset)
      offset += sect._file_size
      self.sections.append(sect)
      
  def __str__(self):
    parent_str = super(MachOSegmentCommand, self).__str__()
    # TODO(glider): different format specifiers for 32-bit?
    result = ('%s\n\tsegname: %s\n\tvmaddr: %x\n\tvmsize: %x\n'
              '\tfileoff: %Ld\n\tfilesize: %Ld\n\tnsects: %d\n') % (
      parent_str, self.segname, self.vmaddr, self.vmsize,
      self.fileoff, self.filesize, self.nsects)
    result += '\n'.join(map(str, self.sections))
    return result

class MachOSection(MachOBase):
  def __init__(self, endian, bits, file_stream, offset):
    super(MachOSection, self).__init__(offset)
    CheckedSeek(file_stream, offset)
    if bits == 64:
      bytes = CheckedRead(file_stream, 80)
      (self.sectname, self.segname, self.addr, self.size,
       self.offset, self.align, self.reloff, self.nreloc,
       self.flags, self.reserved1, self.reserved2,
       self.reserved3) = struct.unpack(endian + '16s16s2Q8I', bytes)
      self._file_size = 80
    else:
      raise MachOError, 'section (32-bit) not implemented'
    CheckedSeek(file_stream, self.offset) 
    self.bytes = CheckedRead(file_stream, self.size)

  def __str__(self):
    result = '\t\tsectname: %s\tsegname: %s\n\t\toffset: %Ld\tsize: %x' % (
      self.sectname, self.segname, self.offset, self.size)
    return result
    
class MachOTextSection(MachOSection):
  def __init__(self, endian, bits, file_stream, offset):
    super(MachOTextSection, self).__init__(endian, bits, file_stream, offset)
    bytes = map(ord, self.bytes)
    D = disassembler.Disassembler(file('increment-nocb.dylib.dump').readlines())
    self.code = D.disassemble(bytes)
  def __str__(self):
    parent_str = super(MachOTextSection, self).__str__()
    return parent_str + str(self.code)

class MachOBinary(object):
  def __init__(self, filename):
    print "Reading Mach-O file from %s" % filename
    self.file_stream = file(filename)
    self.header = MachOHeader(self.file_stream, offset=0)
    offset = self.header._file_size
    self.commands = []
    for i in range(self.header.ncmds):
      lc = MachOLoadCommandFactory(
          self.header.endian, self.header.bits, self.file_stream, offset)
      self.commands.append(lc)
      offset += lc._file_size
      print lc
  def write_to_file(self, file_stream):
    self.header.write_to_file(file_stream)
    for i in range(self.header.ncmds):
      self.commands[i].write_to_file(file_stream)
    file_stream.flush()


def main(argv):
  if len(argv) > 0:
    M = MachOBinary(argv[1])
    out_file = file(argv[1] + '.bak', 'w')
    #M.write_to_file(out_file)
    out_file.close()

if __name__ == "__main__":
  # TODO(glider): doctests?
  main(sys.argv)
