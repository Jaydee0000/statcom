import subprocess
from uuid import uuid4
import pytest
from app.core.config import get_settings


@pytest.fixture
def media(tmp_path, monkeypatch):
    settings = get_settings()
    monkeypatch.setattr(settings, 'video_storage_path', tmp_path / 'uploads')
    sample = tmp_path / 'sample.mp4'
    subprocess.run(['ffmpeg', '-v', 'error', '-f', 'lavfi', '-i', 'color=c=green:s=160x90:r=10',
                    '-t', '12', '-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-movflags', '+faststart', str(sample)], check=True)
    return sample.read_bytes()


def upload(client, graph, media, **data):
    return client.post('/api/v1/videos/upload', data={'match_id': graph['match']['id'], **data},
                       files={'file': ('first half.mp4', media, 'video/mp4')})


def test_upload_metadata_multiple_and_range(client, graph, media, db):
    from app.models import Video
    first = upload(client, graph, media, period='second_half', match_time_offset='2700', video_time_offset='5')
    assert first.status_code == 201, first.text
    video = first.json()
    assert video['match_id'] == graph['match']['id']
    assert video['original_filename'] == 'first half.mp4'
    assert video['storage_key'] != video['original_filename']
    assert video['file_size'] == len(media)
    assert video['mime_type'] == 'video/mp4'
    assert video['duration_seconds'] == 12
    assert video['upload_status'] == 'UPLOADED' and video['processing_status'] == 'READY'
    assert video['uploaded_at'] and video['match_time_offset'] == 2700 and video['video_time_offset'] == 5
    assert db.get(Video, uuid4()) is None
    second = upload(client, graph, media).json()
    assert second['id'] != video['id'] and second['match_id'] == video['match_id']
    assert client.get(f"/api/v1/videos/{video['id']}").json()['storage_key'] == video['storage_key']
    path = f"/api/v1/videos/{video['id']}/media"
    assert client.get(path).content == media
    part = client.get(path, headers={'Range': 'bytes=10-99'})
    assert part.status_code == 206 and part.content == media[10:100]
    assert part.headers['content-range'] == f'bytes 10-99/{len(media)}'
    assert client.get(path, headers={'Range': 'bytes=-20'}).content == media[-20:]
    assert client.get(path, headers={'Range': f'bytes={len(media)+1}-'}).status_code == 416
    assert client.head(path).headers['accept-ranges'] == 'bytes'


@pytest.mark.parametrize('name,body,code', [('bad.exe', b'x', 415), ('../bad.mp4', b'x', 422),
    ('bad.mp4', b'not video', 422), ('empty.mp4', b'', 422), ('C:\\bad.mp4', b'x', 422)])
def test_invalid_upload(client, graph, media, name, body, code):
    response = client.post('/api/v1/videos/upload', data={'match_id': graph['match']['id']}, files={'file': (name, body)})
    assert response.status_code == code, response.text
    assert not list(get_settings().video_storage_path.glob('*'))


def test_missing_match_and_file(client, graph, media):
    assert upload(client, graph, media, match_id=str(uuid4())).status_code == 422
    assert client.get(f"/api/v1/videos/{graph['video']['id']}/media").status_code == 404
    assert client.post(f"/api/v1/videos/{graph['video']['id']}/start").status_code == 404


def test_missing_ffprobe_and_size_limit(client, graph, media, monkeypatch):
    settings = get_settings()
    monkeypatch.setattr(settings, 'ffprobe_path', '/missing/ffprobe')
    response = upload(client, graph, media)
    assert response.status_code == 503 and 'ffprobe' in response.text
    assert not list(settings.video_storage_path.glob('*'))
    monkeypatch.setattr(settings, 'video_max_upload_bytes', 10)
    assert upload(client, graph, media).status_code == 413
    assert not list(settings.video_storage_path.glob('*'))


def test_full_session_workflow(client, graph, media):
    video = upload(client, graph, media).json()
    def listed(completed=False):
        return client.get(f'/api/v1/videos/workflow?completed={str(completed).lower()}').json()
    assert listed()[0]['video']['id'] == video['id'] and listed()[0]['session'] is None
    path = f"/api/v1/videos/{video['id']}/start"
    session = client.post(path).json()
    assert session['status'] == 'IN_PROGRESS'
    assert client.post(path).json()['id'] == session['id']
    session_path = f"/api/v1/annotation-sessions/{session['id']}"
    assert client.post('/api/v1/annotation-sessions', json={'video_id': video['id'], 'match_id': video['match_id']}).status_code == 409
    assert client.patch(session_path, json={'last_playback_position': 8.5}).status_code == 200
    assert client.get(session_path).json()['last_playback_position'] == 8.5
    assert client.patch(session_path, json={'last_playback_position': 13}).status_code == 422
    assert client.patch(session_path, json={'last_playback_position': -1}).status_code == 422
    assert listed()[0]['session']['status'] == 'IN_PROGRESS'
    assert client.patch(session_path, json={'status': 'REVIEWED'}).status_code == 409
    assert client.patch(session_path, json={'status': 'READY_FOR_REVIEW'}).status_code == 200
    assert listed()[0]['session']['status'] == 'READY_FOR_REVIEW'
    assert client.post(path).json()['status'] == 'READY_FOR_REVIEW'
    reviewed = client.patch(session_path, json={'status': 'REVIEWED'}).json()
    assert reviewed['completed_at']
    assert listed() == [] and listed(True)[0]['session']['id'] == session['id']
    assert client.post(path).json()['status'] == 'REVIEWED'
    reopened = client.patch(session_path, json={'status': 'IN_PROGRESS'}).json()
    assert reopened['completed_at'] == reviewed['completed_at']
    assert listed(True) == [] and listed()[0]['session']['id'] == session['id']


def test_storage_traversal_not_served(client, create, graph, media):
    video = create('videos', match_id=graph['match']['id'], original_filename='x.mp4', storage_key='../outside.mp4')
    assert client.get(f"/api/v1/videos/{video['id']}/media").status_code == 404
