import csv
import io
import json
import os
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4
from fastapi import FastAPI, File, Form, HTTPException, Query, UploadFile
from fastapi.responses import FileResponse, Response
from fastapi.staticfiles import StaticFiles
from starlette.concurrency import run_in_threadpool
from .engine import Detector, ROOT, MAX_BYTES, decode_image
from .storage import Store

def create_app(db_path=None,weights=None):
    @asynccontextmanager
    async def lifespan(app):
        app.state.detector=Detector(weights)
        app.state.store=Store(db_path or os.getenv('INSPECT_DB',str(ROOT/'runtime/inspections.db')))
        yield

    app=FastAPI(title='InspectAI',version='1.0.0',lifespan=lifespan,
                description='Local educational defect detection on synthetic textures. Not a factory quality certification system.')
    app.mount('/static',StaticFiles(directory=ROOT/'web'),name='static')

    @app.get('/',include_in_schema=False)
    def dashboard(): return FileResponse(ROOT/'web/index.html')

    @app.get('/health')
    def health(): return {'status':'ok','model_loaded':True,'model':'YOLOv8n','scope':'synthetic demo'}

    async def perform(raw,filename,threshold):
        try:
            image=await run_in_threadpool(decode_image,raw)
            result=await run_in_threadpool(app.state.detector.inspect,image,threshold)
        except ValueError as exc: raise HTTPException(400,str(exc)) from exc
        result.update(id=str(uuid4()),created_at=datetime.now(timezone.utc).isoformat(),filename=filename[:200])
        await run_in_threadpool(app.state.store.add,result)
        return result

    @app.post('/api/inspect')
    async def inspect(file:UploadFile=File(...),threshold:float=Form(.35,ge=.05,le=.95)):
        try:
            raw=await file.read(MAX_BYTES+1)
            if len(raw)>MAX_BYTES: raise HTTPException(413,'Image exceeds the 8 MB upload limit.')
            # Treat supplied names as display data only, never as a filesystem path.
            name=(file.filename or 'upload').replace('\\','/').split('/')[-1]
            return await perform(raw,name,threshold)
        finally: await file.close()

    @app.get('/api/samples')
    def samples():
        return [{'name':p.name,'url':'/api/samples/'+p.name} for p in sorted((ROOT/'samples').glob('*.png'))]

    def sample_path(name):
        candidates={p.name:p for p in (ROOT/'samples').glob('*.png')}
        if name not in candidates: raise HTTPException(404,'Sample not found')
        return candidates[name]

    @app.get('/api/samples/{name}')
    def sample_image(name:str): return FileResponse(sample_path(name))

    @app.post('/api/inspect-sample/{name}')
    async def inspect_sample(name:str,threshold:float=Query(.35,ge=.05,le=.95)):
        return await perform(sample_path(name).read_bytes(),name,threshold)

    @app.get('/api/history')
    def history(limit:int=Query(100,ge=1,le=1000)): return app.state.store.history(limit)

    @app.get('/api/summary')
    def summary(): return app.state.store.summary()

    @app.get('/api/model-report')
    def model_report():
        p=ROOT/'reports/evaluation.json'
        if not p.exists(): raise HTTPException(404,'Run python -m scripts.evaluate to generate the report.')
        return json.loads(p.read_text(encoding='utf-8'))

    @app.get('/api/export.csv')
    def export():
        fields=['id','created_at','filename','status','defect_count','max_confidence','inference_ms','threshold']
        buffer=io.StringIO(); writer=csv.DictWriter(buffer,fieldnames=fields,extrasaction='ignore');writer.writeheader()
        for record in app.state.store.history(10000):
            # Neutralize spreadsheet formulas, including leading spaces/tabs.
            # Preserve benign names and leave the stored history unchanged.
            safe_record = dict(record)
            filename = str(safe_record.get('filename') or '')
            if filename.lstrip().startswith(('=', '+', '-', '@')):
                filename = "'" + filename
            safe_record['filename'] = filename
            writer.writerow(safe_record)
        return Response(buffer.getvalue(),media_type='text/csv',headers={'Content-Disposition':'attachment; filename="inspections.csv"'})
    return app

app=create_app()
