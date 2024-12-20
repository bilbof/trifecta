from trie import Trie
import tempfile
import json
import os
from datetime import datetime
import threading

class DistributedTrie:
  def __init__(self, config, wal, rangemap, coordinator):
    self.range_tries = {}
    self.config = config
    self.checkpoint_dir = config.current()["checkpoint_dir"]
    self.wal = wal
    self.rangemap = rangemap
    self.coordinator = coordinator
    # TODO: Lock per trie
    self.sem = threading.Semaphore()

  def matches(self, query):
    k_factor = self.config.current()["k_factor"]
    prefix, rem = query[:k_factor], query[k_factor+1:]
    if len(prefix) != k_factor:
      # We don't support prefix search at or below the k-factor
      return []
    preference_list = self.rangemap.nodes_for_key(prefix)
    if self.config.node_id not in preference_list:
      print("Forwarding")
      return self.coordinator.matches(query, preference_list)
    if prefix not in self.range_tries:
      return []
    return self.range_tries[prefix].matches(query)
  
  def add(self, word, commit_to_wal=True):
    # todo: return nice error if fails
    k_factor = self.config.current()["k_factor"]
    prefix, rem = word[:k_factor], word[k_factor+1:]
    if len(prefix) != k_factor:
      # we dont support words less than k factor
      return
    preference_list = self.rangemap.nodes_for_key(prefix)
    # TODO: Forward to other nodes if not already forwarding and replication_factor > 1
    # right now we *only* forward if we hit the wrong node (same for remove)
    if self.config.node_id not in preference_list and commit_to_wal:
      print("I'm not coordinator, forwarding")
      return self.coordinator.add(word, preference_list)
    self.sem.acquire()
    self.wal.commit("add", word)

    if prefix not in self.range_tries:
      self.range_tries[prefix] = Trie()
    trie = self.range_tries[prefix]
    trie.add(word)
    self.sem.release()
    return True
  
  def remove(self, word, commit_to_wal=True):
    k_factor = self.config.current()["k_factor"]
    prefix, rem = word[:k_factor], word[k_factor+1:]
    if len(prefix) != k_factor or prefix not in self.range_tries:
      # we dont support words less than k factor
      return
    preference_list = self.rangemap.nodes_for_key(prefix)
    if self.config.node_id not in preference_list and commit_to_wal:
      print("I'm not coordinator, forwarding")
      return self.coordinator.remove(word, preference_list)
    self.sem.acquire()
    self.wal.commit("remove", word)
    trie = self.range_tries[prefix]
    trie.remove(word)
    self.sem.release()
    return True
  
  def is_coordinator_for_key(self, key):
    return self.config.node_id in self.rangemap.nodes_for_key(key)
  
  def load(self, prefix, trie_dict):
    trie = Trie()
    trie.load(trie_dict)
    self.range_tries[prefix] = trie
  
  def replay_wal(self):
    for action, word in self.wal.readlines():
      match action:
        case "add": self.add(word, commit_to_wal=False)
        case "remove": self.remove(word, commit_to_wal=False)
        case _: print(f"Unrecognized action in WAL {action} for word {word}")