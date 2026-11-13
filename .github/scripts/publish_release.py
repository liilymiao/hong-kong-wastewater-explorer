"""Publish the reviewed release commit only after checking every asset digest."""
from pathlib import Path
import hashlib
import json
import os
import re
import subprocess
import time

TAG = 'v1.6.4'
REPO = os.environ['GH_REPO']
metadata = json.loads(Path(f'release/{TAG}/release.json').read_text())
COMMIT = metadata['commit']
if metadata['tag'] != TAG or not re.fullmatch(r'[0-9a-f]{40}', COMMIT):
    raise RuntimeError('Invalid reviewed release identity')
NAMES = {'project.zip', 'course-python.zip', 'report.pdf', 'proposal-english.mp4',
         'proposal-subtitled.mp4', 'acceptance.zip', 'SHA256SUMS.txt'}
if set(metadata['assets']) != NAMES:
    raise RuntimeError('Expected exactly seven reviewed release assets')


def gh(*args):
    return subprocess.check_output(['gh', *args], text=True)


def api(path):
    return json.loads(gh('api', f'repos/{REPO}/{path}'))


assets = [Path('release-out') / name for name in sorted(NAMES)]
expected = {name: (entry['bytes'], 'sha256:' + entry['sha256'])
            for name, entry in metadata['assets'].items()}
local = {p.name: (p.stat().st_size, 'sha256:' + hashlib.sha256(p.read_bytes()).hexdigest())
         for p in assets}
if local != expected:
    raise RuntimeError('Local assets differ from the reviewed release checksums')

refs = api(f'git/matching-refs/tags/{TAG}')
tag = next((r for r in refs if r['ref'] == f'refs/tags/{TAG}'), None)
if tag is None:
    tag = json.loads(gh('api', '--method', 'POST', f'repos/{REPO}/git/refs',
                       '-f', f'ref=refs/tags/{TAG}', '-f', f'sha={COMMIT}'))
if tag['object']['sha'] != COMMIT:
    raise RuntimeError('Existing tag points to another commit; refusing to alter it')


def find_release(wait_seconds=0):
    """Use the CLI draft-aware lookup, then the numeric REST release ID."""
    deadline = time.monotonic() + wait_seconds
    while True:
        probe = subprocess.run(['gh', 'release', 'view', TAG, '--json', 'databaseId,isDraft'],
                               text=True, capture_output=True)
        if probe.returncode == 0:
            info = json.loads(probe.stdout)
            release_id = int(info['databaseId'])
            try:
                release = api(f'releases/{release_id}')
            except subprocess.CalledProcessError as exc:
                if not any(marker in (exc.output or '').lower() for marker in ('not found', '404')):
                    raise
            else:
                if release['tag_name'] != TAG or release['id'] != release_id:
                    raise RuntimeError('Release identity differs from the requested tag')
                return release
        if probe.returncode != 0:
            error = (probe.stderr + probe.stdout).lower()
            if not any(marker in error for marker in ('not found', '404')):
                raise RuntimeError('Cannot look up release: ' + probe.stderr.strip())
        if time.monotonic() >= deadline:
            return None
        time.sleep(min(2, max(0, deadline - time.monotonic())))


release = find_release()
if release is None:
    try:
        gh('release', 'create', TAG, '--draft', '--verify-tag', '--target', COMMIT,
           '--title', 'v1.6.4 — Verified comparisons and final acceptance',
           '--notes-file', f'release/{TAG}/notes.md')
    except subprocess.CalledProcessError:
        # A previously created draft may become visible after the first lookup.
        release = find_release(wait_seconds=20)
        if release is None:
            raise
    else:
        release = find_release(wait_seconds=20)
if release is None:
    raise RuntimeError('Created release cannot be found after 20 seconds')
release_id = release['id']
was_draft = release['draft']
if was_draft:
    gh('release', 'upload', TAG, *[str(p) for p in assets], '--clobber')
deadline = time.monotonic() + (20 if was_draft else 0)
while True:
    release = api(f'releases/{release_id}')
    received = {a['name']: (a['size'], a.get('digest')) for a in release['assets']}
    if received == expected:
        break
    if time.monotonic() >= deadline:
        raise RuntimeError('Published asset inventory or checksum mismatch')
    time.sleep(min(2, max(0, deadline - time.monotonic())))
if release['draft']:
    gh('release', 'edit', TAG, '--draft=false', '--latest')
deadline = time.monotonic() + 20
while True:
    release = api(f'releases/{release_id}')
    if not release['draft']:
        break
    if time.monotonic() >= deadline:
        raise RuntimeError('Release remains a draft after publication request')
    time.sleep(min(2, max(0, deadline - time.monotonic())))
print(json.dumps({'tag': TAG, 'commit': COMMIT, 'assets_verified': len(assets),
                  'url': release['html_url']}))
