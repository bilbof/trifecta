import httpx
import random

class Coordinator:
  def __init__(self, config, cluster, rangemap, local_trie):
    self.config = config
    self.cluster = cluster
    self.rangemap = rangemap
    self.local_trie = local_trie

  def matches(self, query):
    preference_list = self.preference_list(query)
    if self.config.node_id in preference_list:
      return self.local_trie.matches(query)
    node = self.random_healthy_node(preference_list)
    if not node: return []
    try:
      req = httpx.get(f"{node}/search", params={"q": query})
      if req.status_code == 200:
        return req.json()
    except Exception as err:
      print(f"Unexpected {err=}, when proxying to {node} with query {query} {type(err)=}")
      return []

  def add(self, word):
    return self._write_word("POST", word)
  
  def remove(self, word):
    return self._write_word("DELETE", word)
  
  def preference_list(self, word):
    k_factor = self.config.current()["k_factor"]
    prefix, rem = word[:k_factor], word[k_factor+1:]
    if len(prefix) != k_factor:
      # We don't support word lengths at or below the k-factor
      return []
    return self.healthy_nodes(self.rangemap.nodes_for_key(prefix))

  def healthy_nodes(self, nodes):
    if len(nodes) == 0: return set()
    pnodes = self.cluster.nodes
    return set([node["host"] for node in pnodes if node["host"] in nodes and node["status"]["healthy"]])

  def random_healthy_node(self, node_hosts):
    nodes = []
    # todo change cluster.nodes to hash
    for node in self.cluster.nodes:
      if node["host"] in node_hosts and node["status"]["healthy"]: nodes.append(node["host"])
    if len(nodes) == 0: return
    return random.choice(nodes)

  def _write_word(self, method, word):
    # TODO: keep tombstone (and check at coordinator if in local tombstone before sending unnecessary reqs)
    # TODO: this whole thing is gross
    preference_list = self.preference_list(word.word)
    if len(preference_list) == 0: return False
    no_failures = True
    quorum = int((self.config.replication_factor / 2) + 1) # todo: allow configuring quorum separately
    is_member = self.config.node_id in preference_list
    if self.config.node_id in preference_list:
      quorum -= 1
      no_failures = no_failures and self.local_write(method, word.word)
    
    if quorum > 0 and no_failures and word.gossip:
      visited = set()
      if is_member:
        visited.add(self.config.node_id)
      # TODO: send in parallel, handle failures (try another node if one fails, sloppy quorum etc)
      # TODO: rollbacks
      for node in preference_list:
        if node in visited: continue
        if quorum <= 0: return True
        quorum -= 1
        self._proxy_request(method, f"{node}/api/v1/words", { "word": word.word, "gossip": False })  
    return quorum <= 0 and no_failures
    
  def local_write(self, method, word):
    match method:
      case "POST":
        return self.local_trie.add(word)
      case "DELETE":
        return self.local_trie.remove(word)
      case _:
        return False

  def _proxy_request(self, method, path, word, data=None):
    try:
      code = httpx.request(method, f"{node}/api/v1/words", data=data).status_code
      if code >= 200 and code < 300: return True
    except Exception as err:
      print(f"Unexpected {err=}, when proxying {method} to {node} with word {word} {type(err)=}")
      return False