# TODO

* Distributed writes
    * Version tries (keep a timestamp of last write on keys and share timestamp)
        * Last write wins
        * Treat a subtrie as an object. Send whole trie in write forwards

---

* Gossip versions and trigger background updates
    * Every second pick a random replica and request timestamps+hashes for tries, if any are out of sync replica requests the hashes from node
    * Keep tombstones of deleted keys so when we do a merge we don't bring back deleted data.
    * Clean up tombstones after a configurable number of days
* Adding a new node to the cluster
    * Rangemap versioning
    * Wait for configuration of ring to be agreed upon by all nodes before triggering reshard
    * Current rangemap version should be used for reads until resharding completes
    * Reshard: each node checks if the tries it has are the tries it should own. if not it sends them to a node that should own them (batch write)
    * On receipt of a batch write, node forwards to peers. Means we have quorum**2 requests during a reshard (fix later)
* Removing a node from the cluster
    * Reverse of adding a node
* Node goes down and then rejoins the cluster
    * Use sloppy quorum and hinted handoff (queue of writes) if we can't get to quorum
* Tests + types + error messages
* Address todos
* Logging + metrics + stats page
* Limits and pagination
* Parallel writes, aborts, hedging
* Rollback writes if quorum fails

---------------------------

Ideas

1. Support searching / word size under k-factor
1. CLI
1. Live example
1. Example Kubernetes manifests
1. Proxy requests to nodes same zone
1. We assume node clocks are in sync
1. A shard-aware client that skips one potential hop
1. Namespacing and/or word tagging
1. Sorting (popularity:desc, alphabetical:desc)
1. Concurrent healthchecks / gossips
1. Expected that client will handle locking etc. and user will configure trifecta for use case (i.e. writes to triedb should be done in sequence by clients), but maybe we can handle this for them (by versioning/tombstoning words, not tries)