# RangeMap handles dividing up the prefix ranges into balanced chunks and returning the node responsible
# for a given range i.e. (AAA) -> abc
import itertools
import hashlib
import bisect
# TODO: Handle nodes that are "dead" or whatever
# Do something smarter with node ids (rather than b64'd hostnames)
class RangeMap:
  def __init__(self, cluster, config):
    self.cluster = cluster
    self.config = config
  
  def prefix_to_nodes(self, prefix):
    hash_value = self.hash(prefix)
    return self.cluster.nodes[hash_value % len(self.cluster.nodes)]
  
  def node_name_to_id(self, node_name):
    return hashlib.md5(bytes(node_name, "utf-8")).hexdigest()

  def hash(self, str):
    return int(hashlib.md5(str.encode("utf-8")).hexdigest(), 16)

  def nodes_for_key(self, key):
    """
    Returns <replication_factor> distinct physical nodes for the given key.
    """
    # TODO: make topology aware by passing in zone of each node
    # then check if physical node is in zone that we have visited
    replication_factor = self.config.replication_factor
    # todo: use node id not host
    nodes = [node["host"] for node in self.cluster.nodes]
    vnodes = self.cluster.virtual_nodes
    sorted_hashes = self.cluster.sorted_vnode_hashes

    if len(nodes) <= replication_factor:
      return nodes

    hash_value = self.hash(key)
    visited_nodes = set()
    result = []

    # find the starting index using binary search
    start_index = bisect.bisect_left(sorted_hashes, hash_value)

    # traverse the ring to collect distinct physical nodes
    for i in range(len(sorted_hashes)):
      # todo: probably a better way to do this - maybe i can skip as in dynamo, maybe node hash
      # tokens can be contiguous then we skip by just do vnode += vnodes_per_node
      # but that may not work for topology-awareness...
      vnode = sorted_hashes[(start_index + i) % len(sorted_hashes)]
      physical_node = vnodes[vnode]
      if physical_node not in visited_nodes:
        visited_nodes.add(physical_node)
        result.append(physical_node)
      if len(result) == replication_factor:
        break

    return result

  def node_prefixes(self, node):
    return [
      "".join(prefix)
      for prefix in self.combinations()
      if node in self.node_id("".join(prefix))
    ]

  def combinations(self):
    return itertools.product(self.config.current()["lexicon"], repeat=self.config.current()["k_factor"])

# from config import Config
# from cluster import Cluster
# config = Config("config.yaml")
# cluster = Cluster(config)
# rangemap = RangeMap(cluster, config)

# import string
# for key in string.ascii_uppercase:
#   result_nodes = rangemap.nodes_for_key(key)
#   print(f"Nodes for key '{key}': {result_nodes}")
