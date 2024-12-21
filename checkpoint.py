from datetime import datetime
import time
import tempfile
import json
import os
import glob

class Checkpoint:
  def __init__(self, config, sharded_trie):
    self.config = config
    self.sharded_trie = sharded_trie
    self.dir = config.current()["checkpoint_dir"]
    self._ensure_dir()

  def load(self):
    last = self.last()
    if not last:
      return False
    with open(last, 'r') as f:
      for line in f.readlines():
        prefix, object = line.rstrip().split(" ", maxsplit=1)
        trie_dict = json.loads(object)
        self.sharded_trie.load(prefix, trie_dict)
    return True


  def save(self):
    checkpointed = False
    timestamp = str(int(time.time() * 100))
    tmp = open(os.path.join(os.getcwd(), self.dir, timestamp), "a+")
    try:
      for prefix, trie in self.sharded_trie.range_tries.items():
        print(f"{prefix} {json.dumps(trie.dict())}", file=tmp)
      checkpointed = True
    finally:
      if checkpointed:
        checkpoint_path = os.path.join(os.getcwd(), self.dir, f"chk_{timestamp}")
        print(f"Saving checkpoint to {checkpoint_path}")
        os.rename(tmp.name, checkpoint_path)
        self.cleanup()
      else:
        print(f"Failed to checkpoint {timestamp}")
      tmp.close()

  def cleanup(self):
    count = self.config.current()["keep_n_checkpoints"]
    globbed = sorted(glob.glob(os.path.join(os.getcwd(), self.dir, "chk_*")))
    to_delete = globbed[:-count]
    # TODO[cleanup]: Debug mode
    print(f"Deleting {len(to_delete)} checkpoints. Keeping {len(globbed[-count:])}.")
    for f in to_delete:
      print(f"Deleting {f}")
      os.remove(f)

  def last(self):
    globbed = sorted(glob.glob(os.path.join(os.getcwd(), self.dir, "chk_*")))
    if len(globbed) == 0:
      return
    return globbed[-1]
  
  def _ensure_dir(self):
    path = os.path.join(os.getcwd(), self.dir)
    if os.path.exists(path):
      if not os.path.isdir(self.dir):
        raise Exception(f"Checkpoint location {self.dir} exists but is not a directory")
    else:
      os.mkdir(path)


# from config import Config
# from sharded_trie import ShardedTrie
# from wal import Wal

# config = Config("config.yaml")
# wal = Wal(config)
# trie = ShardedTrie(config, wal)

# trie.add("twitter")
# trie.add("twitch")
# trie.add("twilight")
# trie.add("twinky")
# trie.add("twigs")
# trie.add("twig")
# trie.add("tough")
# trie.add("thought")

# checkpointer = Checkpoint(config, trie)

# checkpointer.save()

# print(f"Last checkpoint: {checkpointer.last()}")
