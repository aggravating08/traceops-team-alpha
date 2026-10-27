"""A minimal Meterless World Model implementation, not an official SDK.

WorldStoreService + IngestPipelineService + ContextBuilderService.
Append-only content-addressed observations; each run pins its exact observations.
Canonical state is reconstructed on read, and agents consume shared context.
"""
import hashlib
import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path


def stamp():
    return datetime.now(timezone.utc).isoformat()


def stable_id(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':')).encode()).hexdigest()[:24]


class WorldStoreService:
    def __init__(self, path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.connect() as db:
            db.executescript('''
                PRAGMA journal_mode=WAL;
                CREATE TABLE IF NOT EXISTS metadata (key TEXT PRIMARY KEY, value TEXT);
                INSERT OR IGNORE INTO metadata VALUES ('schema_version','1');
                CREATE TABLE IF NOT EXISTS observations (
                  id TEXT PRIMARY KEY, entity_id TEXT, source TEXT, record_key TEXT,
                  payload TEXT, observed_at TEXT, agent_id TEXT);
                CREATE INDEX IF NOT EXISTS obs_entity ON observations(entity_id);
                CREATE TABLE IF NOT EXISTS run_observations (
                  run_id TEXT, observation_id TEXT, PRIMARY KEY(run_id, observation_id));
                CREATE TABLE IF NOT EXISTS runs (
                  id TEXT PRIMARY KEY, created_at TEXT, question TEXT, status TEXT, result TEXT);
                CREATE TABLE IF NOT EXISTS events (
                  id INTEGER PRIMARY KEY, run_id TEXT, at TEXT, agent TEXT, kind TEXT, payload TEXT);
                CREATE INDEX IF NOT EXISTS events_run ON events(run_id);
            ''')

    def connect(self):
        db = sqlite3.connect(self.path, timeout=15)
        db.row_factory = sqlite3.Row
        return db

    def start(self, run_id, question):
        with self.connect() as db:
            db.execute('INSERT INTO runs VALUES (?,?,?,?,?)', (run_id, stamp(), question, 'running', None))

    def event(self, run_id, agent, kind, payload):
        with self.connect() as db:
            db.execute('INSERT INTO events(run_id,at,agent,kind,payload) VALUES (?,?,?,?,?)',
                       (run_id, stamp(), agent, kind, json.dumps(payload)))

    def finish(self, run_id, result, status='complete'):
        with self.connect() as db:
            db.execute('UPDATE runs SET status=?, result=? WHERE id=?', (status, json.dumps(result), run_id))

    def get(self, run_id):
        with self.connect() as db:
            row = db.execute('SELECT * FROM runs WHERE id=?', (run_id,)).fetchone()
        if not row:
            return None
        return {**dict(row), 'result': json.loads(row['result']) if row['result'] else None}

    def history(self):
        with self.connect() as db:
            return [dict(r) for r in db.execute('SELECT id,created_at,question,status FROM runs ORDER BY created_at DESC LIMIT 50')]

    def events(self, run_id):
        with self.connect() as db:
            return [{**dict(r), 'payload': json.loads(r['payload'])} for r in db.execute('SELECT * FROM events WHERE run_id=? ORDER BY id', (run_id,))]

    def health(self):
        with self.connect() as db:
            return {t: db.execute(f'SELECT COUNT(*) FROM {t}').fetchone()[0] for t in ('observations', 'runs', 'events')}


class IngestPipelineService:
    def __init__(self, store):
        self.store = store

    def ingest(self, run_id, sources, mode):
        keys = {'orders': 'order_id', 'inventory': 'sku', 'tickets': 'ticket_id'}
        # Single transaction: interruption leaves either a full snapshot or no snapshot.
        with self.store.connect() as db:
            for source, rows in sources.items():
                seen = set()
                for row in rows:
                    key = str(row[keys[source]])
                    if key in seen:
                        raise ValueError(f'Duplicate {source} record key: {key}')
                    seen.add(key)
                    obs_id = stable_id([mode, source, key, row])
                    entity = stable_id([mode, source, key])
                    db.execute('INSERT OR IGNORE INTO observations VALUES (?,?,?,?,?,?,?)',
                               (obs_id, entity, source, key, json.dumps(row), stamp(), 'collector'))
                    db.execute('INSERT OR IGNORE INTO run_observations VALUES (?,?)', (run_id, obs_id))
        self.store.event(run_id, 'collector', 'world.ingested', {
            'engine': 'Meterless World Model / minimal implementation', 'mode': mode,
            'counts': {k: len(v) for k, v in sources.items()}, 'schema_version': 1,
            'wired': ['content-addressed observations', 'transactional snapshot', 'run-scoped context', 'source provenance'],
            'not_implemented': ['enrichment queue', 'supervisor agent', 'H-MEM', 'Markovian engine']})


class ContextBuilderService:
    def __init__(self, store):
        self.store = store

    def build(self, run_id, order_id=None, region=None, sku=None, limit=200):
        with self.store.connect() as db:
            all_rows = [dict(r) for r in db.execute('''SELECT o.* FROM observations o
                 JOIN run_observations r ON r.observation_id=o.id WHERE r.run_id=? ORDER BY o.source,o.record_key''', (run_id,))]
        grouped = {s: [] for s in ('orders', 'inventory', 'tickets')}
        for row in all_rows:
            record = json.loads(row['payload'])
            grouped[row['source']].append({'citation': row['id'], 'entity_id': row['entity_id'],
                'source': row['source'], 'key': row['record_key'], 'record': record,
                'selection_reason': 'exact run snapshot'})
        orders = [o for o in grouped['orders'] if (not order_id or o['key'].upper() == order_id.upper())
                  and (not region or o['record']['region'].lower() == region.lower())
                  and (not sku or o['record']['sku'].upper() == sku.upper())]
        selected = orders[:limit]
        ids = {o['key'] for o in selected}
        skus = {o['record']['sku'] for o in selected}
        context = {'orders': selected,
                   'inventory': [r for r in grouped['inventory'] if r['key'] in skus],
                   'tickets': [r for r in grouped['tickets'] if r['record']['order_id'] in ids],
                   'truncated': len(orders) > limit,
                   'scope': {'order_id': order_id, 'region': region, 'sku': sku}}
        self.store.event(run_id, 'context-builder', 'context.selected', {
            'scope': context['scope'], 'counts': {k: len(context[k]) for k in grouped},
            'truncated': context['truncated'], 'strategy': 'exact identifiers, then related inventory and tickets',
            'citations': [r['citation'] for s in grouped for r in context[s]]})
        return context
