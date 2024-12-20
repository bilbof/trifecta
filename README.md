# Trifecta

Distributed Trie database.

This is WIP for a personal project.

## API

```
POST /api/v1/words { "word": "trifecta" }
POST /api/v1/words { "word": "tribute" }
POST /api/v1/words { "word": "trinket" }
POST /api/v1/words { "word": "triumph" }
POST /api/v1/words { "word": "trial" }
POST /api/v1/words { "word": "triathlon" }

GET /search?q=tria => {"results":["trial","triathlon"]}
GET /search?q=triat => {"results":["triathlon"]}
```

## Examples

```shell
curl -X POST http://localhost:8000/api/v1/words -d '{"word":"foo"}' -H "Content-Type: application/json"

curl -X DELETE http://localhost:8000/api/v1/words -d '{"word":"foo"}' -H "Content-Type: application/json"
```

## Distribution

This will eventually be a distributed trie. Right now it's just a single node triedb.

**Eventual design**

Since tries are divided up into a subtries (using k-length prefixes) we can treat these prefixes and subtries as key-values and run a cassandra/dynamo like system to spread tries around a balanced ring.

Trifecta provides an API to a persistent, distributed trie. The trie in theory can be so large that it requires spreading it across many nodes (e.g. bitly paths, or a db of a large number of strings requiring autocomplete).

A node in the ring owns some portion of the trie. The size of these portions is decided by the k-factor. When a node receives a read/write it forwards it if necessary to a node owner (ideally in same zone). This is a masterless system, like dynamo (not dynamodb) so you should be able to write to any node.

Increasing k-factor decreases memory usage of tries (since trie can be split into smaller shards) at a cost of slightly increasing memory usage of coordinator (rangemap). Main issue is functional since you can't currently search for a trie with a length less than the k-factor.

## Developing locally

```sh
source .venv/bin/activate
uv pip install -r requirements.txt
```