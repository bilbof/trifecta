# RangeMap handles dividing up the prefix ranges into balanced chunks and returning the node responsible
# for a given range i.e. (AAA) -> abc
import itertools
import hashlib

# TODO: Handle nodes that are "dead" or whatever
# Do something smarter with node ids (rather than b64'd hostnames)
class RangeMap:
  def __init__(self, cluster, config):
    self.cluster = cluster
    self.config = config
  
  def prefix_to_node(self, prefix):
    hash_value = self.hash(prefix)
    return self.cluster.nodes[hash_value % len(self.cluster.nodes)]

  def node_name_to_id(self, node_name):
    # todo: do something better
    return hashlib.md5(bytes(node_name, "utf-8")).hexdigest()

  def hash(self, str):
    return int(hashlib.md5(bytes(str, "utf-8")).hexdigest(), 16)

  def node_id(self, key):
    hash_value = self.hash(key)
    # virtual_nodes is a hmap of virtual node hash values to physical nodes
    # find the closest virtual node clockwise on the ring
    virtual_nodes = sorted(self.cluster.virtual_nodes)
    for vnode in virtual_nodes:
      if hash_value <= vnode:
        return self.cluster.virtual_nodes[vnode]
    return self.cluster.virtual_nodes[virtual_nodes[0]] # We wrap around, such dynamo-ism wow

  def node_prefixes(self, node):
    return [
      "".join(prefix)
      for prefix in self.combinations()
      if self.node_id("".join(prefix)) == node
    ]

  def combinations(self):
    return itertools.product(self.config.current()["lexicon"], repeat=self.config.current()["k_factor"])
