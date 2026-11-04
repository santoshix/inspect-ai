import io
import json
from pathlib import Path
import numpy as np
import pytest
from fastapi.testclient import TestClient
from PIL import Image
from inspection.api import create_app
from inspection.engine import ROOT, MAX_BYTES, decode_image
from inspection.storage import Store
from scripts.generate_data import sample

@pytest.fixture(scope='module')
def client(tmp_path_factory):
    with TestClient(create_app(db_path=tmp_path_factory.mktemp('db')/'test.db')) as client:
        yield client

def png(array=None):
    buf=io.BytesIO();Image.fromarray(array if array is not None else np.full((128,128,3),180,np.uint8)).save(buf,format='PNG');return buf.getvalue()

def test_health_and_dashboard(client):
    assert client.get('/health').json()['model_loaded']
    assert 'InspectAI' in client.get('/').text
    assert client.get('/static/app.js').status_code==200

def test_inspect_and_persistence(client):
    before=client.get('/api/summary').json()['total']
    image=(ROOT/'samples/defect_01.png').read_bytes()
    response=client.post('/api/inspect',files={'file':('part.png',image,'image/png')},data={'threshold':'.35'})
    assert response.status_code==200,response.text
    result=response.json();assert result['defect_count']>0
    assert result['annotated_image'].startswith('data:image/png;base64,')
    assert result['inference_ms']>0
    for d in result['detections']:
        x1,y1,x2,y2=d['box'];assert 0<=x1<=x2<result['width'];assert 0<=y1<=y2<result['height']
    assert client.get('/api/summary').json()['total']==before+1
    assert client.get('/api/history').json()[0]['id']==result['id']

def test_no_defect_sample(client):
    result=client.post('/api/inspect-sample/clean_01.png').json()
    assert result['defect_count']==0
    assert result['status']=='NO DEFECT DETECTED'

def test_invalid_bytes(client):
    assert client.post('/api/inspect',files={'file':('x.png',b'not an image','image/png')}).status_code==400

def test_empty_file(client):
    assert client.post('/api/inspect',files={'file':('x.png',b'','image/png')}).status_code==400

@pytest.mark.parametrize('threshold',['0','1','garbage'])
def test_invalid_threshold(client,threshold):
    assert client.post('/api/inspect',files={'file':('x.png',png(),'image/png')},data={'threshold':threshold}).status_code==422

def test_upload_limit(client):
    assert client.post('/api/inspect',files={'file':('x.png',b'x'*(MAX_BYTES+1),'image/png')}).status_code==413

def test_pixel_limit():
    with pytest.raises(ValueError,match='megapixels'):
        decode_image(png(np.zeros((4001,4000,3),np.uint8)))

def test_unsupported_format():
    buffer=io.BytesIO();Image.new('RGB',(30,30)).save(buffer,format='GIF')
    with pytest.raises(ValueError,match='PNG and JPEG'):decode_image(buffer.getvalue())

def test_csv_formula_escape(client):
    client.post('/api/inspect',files={'file':('=1+1.png',png(),'image/png')})
    response=client.get('/api/export.csv')
    assert response.status_code==200
    assert "'=1+1.png" in response.text

def test_samples_and_missing(client):
    assert len(client.get('/api/samples').json())>=4
    assert client.get('/api/samples/not_here.png').status_code==404
    assert client.post('/api/inspect-sample/not_here.png').status_code==404

def test_report(client):
    report=client.get('/api/model-report').json()
    assert report['test_images']==120
    assert 0<=report['detection']['mAP50']<=1

def test_history_validation(client):
    assert client.get('/api/history?limit=-1').status_code==422

def test_store_survives_reopen(tmp_path):
    store=Store(tmp_path/'db.sqlite')
    row=dict(id='123',created_at='2026-01-01',filename='a.png',status='NO DEFECT DETECTED',
             defect_count=0,max_confidence=0,inference_ms=1,threshold=.35,detections=[])
    store.add(row)
    assert Store(tmp_path/'db.sqlite').history()[0]['id']=='123'

def test_generator_reproducibility():
    a,b=sample(np.random.default_rng(42));c,d=sample(np.random.default_rng(42))
    assert np.array_equal(a,c) and b==d

def test_splits_do_not_overlap():
    import hashlib
    sets=[{hashlib.sha256(p.read_bytes()).hexdigest() for p in (ROOT/'data/images'/s).glob('*.png')}
          for s in ['train','val','test']]
    assert not sets[0]&sets[1] and not sets[0]&sets[2] and not sets[1]&sets[2]


def test_csv_preserves_safe_filename(client):
    response=client.post('/api/inspect',files={'file':('safe_product.png',png(),'image/png')})
    assert response.status_code==200
    csv_result=client.get('/api/export.csv')
    assert csv_result.status_code==200
    import csv as csv_module
    rows=list(csv_module.DictReader(io.StringIO(csv_result.text)))
    assert any(row['filename']=='safe_product.png' for row in rows)


def test_csv_escapes_whitespace_prefixed_formula(client):
    response=client.post('/api/inspect',files={'file':('  =2+2.png',png(),'image/png')})
    assert response.status_code==200
    import csv as csv_module
    rows=list(csv_module.DictReader(io.StringIO(client.get('/api/export.csv').text)))
    assert any(row['filename'].startswith("'  =") for row in rows)
    # Export formatting must not mutate stored history.
    assert any(row['filename']=='  =2+2.png' for row in client.get('/api/history').json())
