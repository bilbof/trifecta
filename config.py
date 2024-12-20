from yaml import load, dump
try:
  from yaml import CLoader as Loader, CDumper as Dumper
except ImportError:
  from yaml import Loader, Dumper

defaults = {
  "heartbeat_interval": 10,
  "checkpoint_interval": 300,
  "keep_n_checkpoints": 3,
  "wal_dir": "trie_wal",
  "checkpoint_dir": "trie_checkpoints",
}

class Config():
  def __init__(self, filepath):
    self.filepath = filepath

  def current(self):
    stream = open(self.filepath, 'r')
    # TODO: cached struct
    return defaults | load(stream, Loader=Loader)

  def heartbeat_interval(self):
    return self.current()["heartbeat_interval"]

  def checkpoint_interval(self):
    return self.current()["checkpoint_interval"]
