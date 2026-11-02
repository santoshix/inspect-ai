import json
import sqlite3
from pathlib import Path

class Store:
    def __init__(self,path):
        self.path=Path(path); self.path.parent.mkdir(parents=True,exist_ok=True)
        with self.connect() as conn:
            conn.execute('''CREATE TABLE IF NOT EXISTS inspections (
                id TEXT PRIMARY KEY, created_at TEXT NOT NULL, filename TEXT NOT NULL,
                status TEXT NOT NULL, defect_count INTEGER NOT NULL, max_confidence REAL NOT NULL,
                inference_ms REAL NOT NULL, threshold REAL NOT NULL, detections TEXT NOT NULL)''')
    def connect(self):
        conn=sqlite3.connect(self.path,timeout=10);conn.row_factory=sqlite3.Row
        return conn
    def add(self,record):
        fields=('id','created_at','filename','status','defect_count','max_confidence','inference_ms','threshold')
        with self.connect() as conn:
            conn.execute('INSERT INTO inspections VALUES (?,?,?,?,?,?,?,?,?)',
                         [record[f] for f in fields]+[json.dumps(record['detections'])])
    def history(self,limit=100):
        with self.connect() as conn:
            rows=conn.execute('SELECT * FROM inspections ORDER BY created_at DESC LIMIT ?', (limit,)).fetchall()
        result=[]
        for row in rows:
            item=dict(row);item['detections']=json.loads(item['detections']);result.append(item)
        return result
    def summary(self):
        with self.connect() as conn:
            row=conn.execute('''SELECT COUNT(*) AS total, COALESCE(SUM(defect_count>0),0) AS flagged,
                COALESCE(AVG(inference_ms),0) AS average_inference_ms FROM inspections''').fetchone()
        return dict(row)
