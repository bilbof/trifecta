from typing import Union
from pydantic import BaseModel, Field
from fastapi import FastAPI, APIRouter
from config import Config
from cluster import Cluster
from rangemap import RangeMap
from datetime import datetime
from contextlib import asynccontextmanager
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
import base64
from sharded_trie import ShardedTrie
from wal import Wal
from checkpoint import Checkpoint
from coordinator import Coordinator

config = Config("config.yaml")
cluster = Cluster(config)
rangemap = RangeMap(cluster, config)
wal = Wal(config)
trie = ShardedTrie(config, wal) # TODO: rename to trieDB
coordinator = Coordinator(config, cluster, rangemap, trie)
checkpointer = Checkpoint(config, trie)
checkpointer.load()
trie.replay_wal()

def node_healthchecks():
  print(f"Checking health of nodes at {datetime.now()}")
  cluster.update_nodes()

def checkpoint():
  print(f"Saving checkpoint at {datetime.now()}")
  checkpointer.save()

# TODO: Periodically reload and cache config

# Set up the scheduler
scheduler = BackgroundScheduler()
trigger = IntervalTrigger(seconds=config.heartbeat_interval())
checkpoint_trigger = IntervalTrigger(seconds=config.checkpoint_interval())
scheduler.add_job(node_healthchecks, trigger)
scheduler.add_job(checkpoint, checkpoint_trigger)
scheduler.start()

app = FastAPI()

# Ensure the scheduler shuts down properly on application exit.
@asynccontextmanager
async def lifespan(app: FastAPI):
  yield
  scheduler.shutdown()

@app.get("/live")
def live():
  return "OK"

@app.get("/ready")
def ready():
  # TODO: Only if node is healthy, has joined ring
  return { "status": "ready" }

@app.get("/")
def read_root():
  # TODO: do something more interesting
  return {"Hello": "World"}

@app.get("/nodes")
def list_nodes():
  return {"nodes": cluster.nodes }

@app.get("/nodes/{node_b64}/ranges")
def node_ranges(node_b64):
  node_name = str(base64.b64decode(node_b64), "utf-8")
  return {"ranges": rangemap.node_prefixes(node_name) }

@app.get("/search/nodes")
def prefix_to_nodes(q: str):
  return {"node": rangemap.nodes_for_key(q) }

@app.get("/search")
def search(q: str):
  return coordinator.matches(q)

# API

api_router = APIRouter(
  prefix="/api/v1",
  tags=["api"],
  responses={404: {"description": "Not found"}},
)

class Word(BaseModel):
  word: str
  gossip: bool = Field(default=True)

@api_router.post("/words")
async def create_word(word: Word):
  # check added strings are in lexicon
  ok = coordinator.add(word)
  if ok:
    return { "message": f"Added '{word.word}' to Trifecta db" }
  else:
    return { "error": f"Did not add '{word.word}' to Trifecta db" }

@api_router.delete("/words")
async def delete_word(word: Word):
  ok = coordinator.remove(word)
  if ok:
    return { "message": f"Removed '{word.word}' to Trifecta db" }
  else:
    return { "error": f"Did not remove '{word.word}' to Trifecta db" }


app.include_router(api_router)

if __name__ == "__main__":
  import uvicorn
  uvicorn.run(app, host="0.0.0.0", port=os.getenv("PORT", 8000))
