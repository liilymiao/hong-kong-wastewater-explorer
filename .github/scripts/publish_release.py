"""Publish only this release after checking commit identity and asset digests."""
from pathlib import Path
import hashlib
import json
import os
import subprocess

TAG = 'v1.6.3'
REPO = os.environ['GH_REPO']
COMMIT = os.environ['GITHUB_SHA']

def gh(*args):
    return subprocess.check_output(['gh', *args], text=True)

def api(path):
    return json.loads(gh('api', f'repos/{REPO}/{path}'))

assets = sorted(Path('release-out').glob('*'))
assets = [p for p in assets if p.name in {
    'project.zip', 'course-python.zip', 'report.pdf', 'proposal-english.mp4',
    'proposal-subtitled.mp4', 'SHA256SUMS.txt'}]
if len(assets) != 6:
    raise RuntimeError('Expected six release assets')
expected = {p.name: (p.stat().st_size, 'sha256:' + hashlib.sha256(p.read_bytes()).hexdigest()) for p in assets}
refs = api(f'git/matching-refs/tags/{TAG}')
tag = next((r for r in refs if r['ref'] == f'refs/tags/{TAG}'), None)
if tag is None:
    tag = json.loads(gh('api', '--method', 'POST', f'repos/{REPO}/git/refs',
                       '-f', f'ref=refs/tags/{TAG}', '-f', f'sha={COMMIT}'))
if tag['object']['sha'] != COMMIT:
    raise RuntimeError('Existing tag points to another commit; refusing to alter it')
def find_release():
    return next((r for r in api('releases?per_page=100') if r['tag_name'] == TAG), None)
release = find_release()
if release is None:
    gh('release', 'create', TAG, '--draft', '--verify-tag',
       '--title', 'v1.6.3 — Course workflow and reproducibility',
       '--notes-file', 'release/v1.6.3/notes.md')
    release = find_release()
if release is None:
    raise RuntimeError('Created release cannot be found')
release_id = release['id']
if release['draft']:
    gh('release', 'upload', TAG, *[str(p) for p in assets], '--clobber')
release = api(f'releases/{release_id}')
received = {a['name']: (a['size'], a.get('digest')) for a in release['assets']}
if received != expected:
    raise RuntimeError('Published asset inventory or checksum mismatch')
if release['draft']:
    gh('release', 'edit', TAG, '--draft=false', '--latest')
release = api(f'releases/{release_id}')
assert not release['draft']
print(json.dumps({'tag': TAG, 'commit': COMMIT, 'assets_verified': len(assets), 'url': release['html_url']}))
