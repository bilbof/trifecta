# Manages the append-only Write Ahead Log.
# Format:
# <operation (1 byte)> <key length (4 bytes)> <key (variable length)>
# Example:
# ADD twitch -> 0x01 0x00 0x00 0x00 0x06 twitch
# REMOVE twitch -> 0x02 0x00 0x00 0x00 0x06 twitch
# WAL rotates once they hit 16mb limit (TODO: allow configuring)
# For now I've implmented this in an easy to debug way

import os
import glob

class Wal:
  def __init__(self, config):
    self.config = config
    self.dir = self.config.current()["wal_dir"]
    self._ensure_wal_dir()
    self.segment = self._max_segment() # "wal_004"
    self._ensure_wal_file()
  
  # TODO: Switch to binary format
  def commit(self, action, object):
    with open(self.wal_file(), "a") as f:
      print(f"{action} {object}", file=f)
  
  def readlines(self):
    globbed = sorted(glob.glob(os.path.join(os.getcwd(), self.dir, "wal_*")))
    for walfile in globbed:
      with open(walfile, 'r') as f:
        for line in f.readlines():
          action, object = line.rstrip().split(" ", maxsplit=1)
          yield (action, object)

  def rotate(self):
    # Rotates WAL and current segment if size limit (16MB) is hit
    # Expected to be called every N seconds
    # If we hit wal_999 we go back to wal_000
    # All rotating does is create a new wal file and set self.segment. Lock-free action. Right?
    if not os.path.getsize(self.wal_file()) > 16000000:
      return # 16MB not yet hit (todo: do infrequently, like every N writes since going over isn't a big deal)
    segment = self.segment.split("wal_")[1]
    self.segment = "wal_" + str((int(segment) + 1) % 1000).zfill(3)
    self._ensure_wal_file()

  def _max_segment(self):
    files = sorted(glob.glob(os.path.join(os.getcwd(), self.dir, "wal_*")))
    if len(files) == 0:
      return "wal_001"
    else:
      return files[-1].split("/")[-1]
  
  def wal_file(self):
    return os.path.join(os.getcwd(), self.dir, f"{self.segment}")
  
  def _ensure_wal_file(self):
    if not os.path.exists(self.wal_file()):
      open(self.wal_file(), 'a').close()

  def _ensure_wal_dir(self):
    path = os.path.join(os.getcwd(), self.dir)
    if os.path.exists(path):
      if not os.path.isdir(self.dir):
        raise Exception(f"WAL location {self.dir} exists but is not a directory")
    else:
      os.mkdir(path)

#
# ======================
#

# from config import Config
# config = Config("config.yaml")
# wal = Wal(config)

# wal.commit("add", "twitter")
# wal.commit("add", "twitch")
# wal.commit("add", "twigs")
# wal.rotate()
# wal.commit("add", "twilight")
# wal.commit("remove", "twigs")

# for action, word in wal.readlines():
#   print(f"{(action, word)}")