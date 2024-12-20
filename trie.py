class Trie:
  def __init__(self):
    self.children = {}
    self.leaf = False

  def matches(self, str):
    return self._matches(str, "")
      
  def _matches(self, str, prefix):
    has_more = len(str) > 0
    has_children = len(self.children) > 0

    if not has_more and not has_children:
      return [prefix]
    if has_more and (not has_children or str[0] not in self.children):
      return []
    if has_more and has_children:
      return self.children[str[0]]._matches(str[1:], prefix + str[0])
    if not has_more and has_children:
      l = []
      if self.leaf:
        l = [prefix]
      for k, child in self.children.items():
        l += child._matches("", prefix + k) 
      return l

  def add(self, str):
    if str == "":
      self.leaf = True
      return
    char = str[0]
    if char not in self.children:
      self.children[char] = Trie()
    self.children[char].add(str[1:])

  def load(self, trie_dict):
    for k, v in trie_dict.items():
      if k == "$":
        self.leaf = True
      else:
        trie = Trie()
        trie.load(v)
        self.children[k] = trie

  def remove(self, str):
    if str == "":
      return
    def _remove(str, trie, i=0):
      if len(str) == i:
        # we found the leaf
        trie.leaf = False
        return len(trie.children) == 0
      
      # we haven't yet found the leaf
      if _remove(str, trie.children[str[i]], i+1):
        del trie.children[str[i]]
        # it's not a leaf and only direct child was removed so this one can be too
        return not trie.leaf and len(trie.children) == 0
      return False

    _remove(str, self)

  
  def dict(self):
    children = { k : v.dict() for k,v in self.children.items()}
    if self.leaf:
      # {$:1} indicates leaf / the end of a valid string
      # todo: this prevents using $ in lexicon, should be configurable or use diff data structure
      return { "$": 1 } | children
    return children
    

# trie = Trie()
# trie.add("twigs")
# trie.add("twig")
# trie.add("twitter")
# trie.add("twitch")
# trie.add("twilight")
# trie.add("twinky")
# # trie.add("tough")
# # trie.add("thought")

# print("tw", trie.matches("twi"))
# print("twi", trie.matches("twi"))
# print("twit", trie.matches("twit"))
# print("twitt", trie.matches("twitt"))
# # print("th", trie.matches("th"))

# print(trie.dict())

# for i in ["twigs", "twig", "twitter", "twitch", "twilight", "twinky"]:
#   trie.remove(i)
#   print(f"removed {i}")
#   print("tw", trie.matches("twi"))
#   print("twi", trie.matches("twi"))
#   print("twit", trie.matches("twit"))
#   print("twitt", trie.matches("twitt"))