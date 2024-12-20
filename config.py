import os
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
  "replication_factor": 1,
}

class Config():
  def __init__(self, filepath):
    self.filepath = filepath

  @property
  def node_id(self):
    # TODO: something better
    return os.getenv("HOSTNAME", "http://127.0.0.1:8000")

  def current(self):
    stream = open(self.filepath, 'r')
    # TODO: cached struct
    return defaults | load(stream, Loader=Loader)

  def heartbeat_interval(self):
    return self.current()["heartbeat_interval"]

  def checkpoint_interval(self):
    return self.current()["checkpoint_interval"]

  @property
  def replication_factor(self):
    return self.current()["replication_factor"]