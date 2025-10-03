
"""
happy_places.py
A lightweight prototype "Happy Places" (BelongOS) brain.
- SQLite-backed
- Register items, record sightings (co-presence), query last seen and recent neighbors.
Usage:
    from happy_places import HappyPlaces
    hp = HappyPlaces("/path/to/happy_places.db")
    hp.register_item("tag_01", label="left sock")
    hp.record_sighting("tag_01", zone="bedroom_floor", seen_with=["tag_02","tag_03"])
    hp.last_seen("tag_01")
    hp.recent_neighbors("tag_01", limit=5)
"""
import sqlite3, datetime, json

class HappyPlaces:
    def __init__(self, db_path="happy_places.db"):
        self.db_path = db_path
        self._init_db()

    def _connect(self):
        return sqlite3.connect(self.db_path)

    def _init_db(self):
        with self._connect() as c:
            c.execute("""CREATE TABLE IF NOT EXISTS items (
                            item_id TEXT PRIMARY KEY,
                            label TEXT
                        )""")
            c.execute("""CREATE TABLE IF NOT EXISTS sightings (
                            sighting_id TEXT PRIMARY KEY,
                            item_id TEXT,
                            zone TEXT,
                            ts TEXT,
                            metadata TEXT,
                            FOREIGN KEY(item_id) REFERENCES items(item_id)
                        )""")
            c.execute("""CREATE TABLE IF NOT EXISTS co_presence (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            item_a TEXT,
                            item_b TEXT,
                            ts TEXT,
                            zone TEXT
                        )""")
            c.commit()

    def register_item(self, item_id, label=None):
        with self._connect() as c:
            c.execute("INSERT OR IGNORE INTO items(item_id, label) VALUES(?,?)", (item_id, label))
            c.commit()

    def record_sighting(self, item_id, zone=None, ts=None, seen_with=None, metadata=None):
        """Record that item_id was seen in zone at time ts and optionally seen_with other item_ids (co-presence).
        seen_with should be a list of other item_ids (strings).
        """
        if ts is None:
            ts = datetime.datetime.utcnow().isoformat()
        if seen_with is None:
            seen_with = []
        meta_json = json.dumps(metadata or {})
        sighting_id = f"s_{item_id}_{ts}"
        with self._connect() as c:
            c.execute("INSERT OR REPLACE INTO sightings(sighting_id, item_id, zone, ts, metadata) VALUES(?,?,?,?,?)",
                      (sighting_id, item_id, zone, ts, meta_json))
            # create co-presence pairs (item_id with each seen_with entry)
            for other in seen_with:
                # store both directions to make queries simpler
                c.execute("INSERT INTO co_presence(item_a, item_b, ts, zone) VALUES(?,?,?,?)", (item_id, other, ts, zone))
                c.execute("INSERT INTO co_presence(item_a, item_b, ts, zone) VALUES(?,?,?,?)", (other, item_id, ts, zone))
            c.commit()

    def last_seen(self, item_id):
        with self._connect() as c:
            r = c.execute("SELECT ts, zone, metadata FROM sightings WHERE item_id=? ORDER BY ts DESC LIMIT 1", (item_id,)).fetchone()
            if not r:
                return None
            ts, zone, meta = r
            return {"item_id": item_id, "last_seen": ts, "zone": zone, "metadata": json.loads(meta)}

    def recent_neighbors(self, item_id, limit=10):
        """Return a summary of the most recent neighbors seen with item_id."""
        with self._connect() as c:
            rows = c.execute("SELECT item_b, ts, zone FROM co_presence WHERE item_a=? ORDER BY ts DESC LIMIT ?", (item_id, limit)).fetchall()
            return [{"item_id": r[0], "ts": r[1], "zone": r[2]} for r in rows]

    def items(self):
        with self._connect() as c:
            rows = c.execute("SELECT item_id, label FROM items").fetchall()
            return [{"item_id": r[0], "label": r[1]} for r in rows]

    def missing_since(self, days=3):
        """Return items not seen in the last `days` days."""
        cutoff = (datetime.datetime.utcnow() - datetime.timedelta(days=days)).isoformat()
        with self._connect() as c:
            rows = c.execute("SELECT item_id FROM items WHERE item_id NOT IN (SELECT DISTINCT item_id FROM sightings WHERE ts > ?)", (cutoff,)).fetchall()
            return [r[0] for r in rows]
