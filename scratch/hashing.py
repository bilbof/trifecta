# Consistent hashing
import hashlib
import bisect

replication_factor = 3
vnodes_per_node = 10
nodes = ["a", "b", "c", "d", "e"]

def hash(key):
  return int(hashlib.md5(key.encode('utf-8')).hexdigest(), 16)

virtual_nodes = {}

for node in nodes:
  for i in range(vnodes_per_node):
    vnode_key = f"{node}_vnode_{i}"
    vnode_hash = hash(vnode_key)
    virtual_nodes[vnode_hash] = node

virtual_nodes = dict(sorted(virtual_nodes.items()))
sorted_vnode_hashes = sorted(virtual_nodes.keys())

def nodes_for_key(key, nodes, vnodes, sorted_hashes):
  """
  Returns <replication_factor> distinct physical nodes for the given key.
  """
  if len(nodes) <= replication_factor:
    return nodes

  hash_value = hash(key)
  visited_nodes = set()
  result = []

  # Find the starting index using binary search
  start_index = bisect.bisect_left(sorted_hashes, hash_value)

  # Traverse the ring to collect distinct physical nodes
  for i in range(len(sorted_hashes)):
    physical_node = vnodes[sorted_hashes[(start_index + i) % len(sorted_hashes)]]

    if physical_node not in visited_nodes:
      visited_nodes.add(physical_node)
      result.append(physical_node)

    if len(result) == replication_factor:
      break

  return result

import string
for key in string.ascii_lowercase:
  result_nodes = nodes_for_key(key, nodes, virtual_nodes, sorted_vnode_hashes)
  # result_nodes= "f"
  print(f"Nodes for key '{key}': {result_nodes}")
