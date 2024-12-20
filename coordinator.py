import httpx
import random

class Coordinator:
  def __init__(self, config, cluster, rangemap):
    self.config = config
    self.cluster = cluster
    self.rangemap = rangemap

  def matches(self, query, nodes):
    node = self.random_healthy_node(nodes)
    if not node: return []
    try:
      req = httpx.get(f"{node}/search", params={"q": query})
      if req.status_code == 200:
        # todo decode
        return req.json()
    except Exception as err:
      print(f"Unexpected {err=}, when proxying to {node} with query {query} {type(err)=}")
      return []

  def random_healthy_node(self, node_hosts):
    nodes = []
    # todo change cluster.nodes to hash
    for node in self.cluster.nodes:
      if node["host"] in node_hosts and node["status"]["healthy"]: nodes.append(node["host"])
    if len(nodes) == 0: return
    return random.choice(nodes)

  def add(self, word, nodes):
    return self._write_word("POST", nodes, word)
  
  def remove(self, word, nodes):
    return self._write_word("DELETE", nodes, word)
  
  def _write_word(self, method, nodes, word):
    # TODO: proxy in parallel to <replication_factor> healthy nodes, not just one
    node = self.random_healthy_node(nodes)
    if not node: return False
    return self._proxy_request(method, f"{node}/api/v1/words", { "word": word })

  def _proxy_request(self, method, path, word, data=None):
    try:
      code = httpx.request(method, f"{node}/api/v1/words", data=data).status_code
      if code >= 200 and code < 300: return True
    except Exception as err:
      print(f"Unexpected {err=}, when proxying {method} to {node} with word {word} {type(err)=}")
      return False