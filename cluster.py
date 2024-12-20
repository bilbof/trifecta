import httpx
import hashlib
from datetime import datetime
import base64

# TODO: Give nodes states: pending->ok->grace->dead
# For now we assume they are all always healthy
class Cluster():
  def __init__(self, config):
    self.config = config
    self.nodes = []
    self.virtual_nodes = {} # Virtual node hash -> physical node
    self.sorted_vnode_hashes = [] # Virtual node hash ring
    self.update_nodes()
  
  def update_nodes(self):
    # TODO: Give grace period, timeouts
    self.nodes = [
      {
        "id": str(base64.b64encode(bytes(node, "utf-8")),"utf-8"),
        "host": node,
        "ts": datetime.now(),
        "status": self.node_health(node)
      } for node in self.config.current()["nodes"]
    ]
    self._generate_virtual_nodes()
  
  def healthy_nodes(self):
    return [n for n in self.nodes if n["status"]["healthy"]]

  def node_health(self, node):
    try:
      res = httpx.get(f"{node}/ready")
      if res.status_code == 200:
        return {"healthy": True, "message": "ok"}
      return {"healthy": False, "message": f"GET {node}/health returned {res.status_code}"}
    except ConnectionError:
      return {"healthy": False, "message": f"Could not connect to {node}"}
    except Exception as err:
      return {"healthy": False, "message": f"Unexpected {err=}, {type(err)=}"}
  
  def vnodes_per_node(self):
    return self.config.current()["vnodes_per_node"]

  def _generate_virtual_nodes(self):
    """
    Create virtual nodes for each physical node.
    """
    virtual_nodes = {}
    for node in self.nodes:
      for i in range(self.vnodes_per_node()):
        vnode_key = f"{node['host']}_vnode_{i}"
        vnode_hash = self.hash(vnode_key)
        virtual_nodes[vnode_hash] = node['host']
    self.virtual_nodes = dict(sorted(virtual_nodes.items()))
    self.sorted_vnode_hashes = sorted(virtual_nodes.keys())

  def hash(self, key):
    """
    Hash function for consistent hashing.
    """
    return int(hashlib.md5(key.encode('utf-8')).hexdigest(), 16)

  def get_physical_node(self, key):
    """
    Find the physical node responsible for the given key.
    """
    hash_value = self.hash(key)
    for vnode_hash in self.virtual_nodes:
      if hash_value <= vnode_hash:
        return self.virtual_nodes[vnode_hash]
    # Wrap around to the first virtual node
    return next(iter(self.virtual_nodes.values()))
