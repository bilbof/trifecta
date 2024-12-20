# class NodeStatus:
#   PENDING="pending"
#   JOINING="joining"
#   ACTIVE="active"
#   LEAVING="leaving"
#   LEFT="left"

# class Node:
#   STATES = [
#     NodeStatus.PENDING,
#     NodeStatus.JOINING,
#     NodeStatus.ACTIVE,
#     NodeStatus.LEAVING,
#     NodeStatus.LEFT,
#   ]
  
#   def __init__(self, host, status=NodeStatus.PENDING):
#     self.host = host
#     self.status = status

#   @property
#   def id(self):
#     return self.host
