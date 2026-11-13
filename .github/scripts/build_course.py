"""Reconstruct the reviewed Python archive from a preserved release and text overlays."""
from pathlib import Path
import argparse
import hashlib
import json
import zipfile

BASE_SHA256 = '1ee1825bcd3318441b263ed40dbcf869bb6091d1a6ec5e3a1d0cf54166369ef6'
PREFIX = 'MATH7005 Course/'
STAMP = (2026, 11, 13, 0, 0, 0)


def digest(data):
    return hashlib.sha256(data).hexdigest()


def verify_manifest(entries):
    manifest = json.loads(entries['release_manifest.json'])
    records = manifest['files']
    if len(records) != len({r['path'] for r in records}):
        raise ValueError('Duplicate course manifest paths')
    if set(entries) != {r['path'] for r in records} | {'release_manifest.json'}:
        raise ValueError('Course inventory mismatch')
    for record in records:
        content = entries[record['path']]
        if len(content) != record['bytes'] or digest(content) != record['sha256']:
            raise ValueError('Course file differs from manifest: ' + record['path'])
    return manifest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo', type=Path, required=True)
    parser.add_argument('--previous-course', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    spec = json.loads((args.repo / 'release/v1.6.4/course-spec.json').read_text())
    if spec['baseline_zip_sha256'] != BASE_SHA256 or spec['archive_prefix'] != PREFIX:
        raise ValueError('Unexpected baseline course identity')
    if tuple(spec['timestamp']) != STAMP:
        raise ValueError('Unexpected deterministic ZIP timestamp')
    raw = args.previous_course.read_bytes()
    if digest(raw) != BASE_SHA256:
        raise ValueError('Previous course ZIP SHA256 mismatch')
    with zipfile.ZipFile(args.previous_course) as z:
        names = z.namelist()
        if z.testzip() is not None or len(names) != len(set(names)):
            raise ValueError('Invalid previous course ZIP')
        if any(not n.startswith(PREFIX) or '..' in Path(n).parts for n in names):
            raise ValueError('Unexpected previous course archive path')
        entries = {n[len(PREFIX):]: z.read(n) for n in names if not n.endswith('/')}
    verify_manifest(entries)
    protected = {name: digest(data) for name, data in entries.items()
                 if name.startswith(('data/', 'src/', 'outputs/', 'saved_results/'))
                 or name in {'config.yaml', 'frozen_config.json'}}
    overlays = args.repo / 'release/v1.6.4/python-overlay'
    listed = spec['overlay_files']
    if len(listed) != len({r['path'] for r in listed}):
        raise ValueError('Duplicate overlay paths')
    actual = {p.relative_to(overlays).as_posix() for p in overlays.rglob('*') if p.is_file()}
    if actual != {r['path'] for r in listed}:
        raise ValueError('Overlay inventory mismatch')
    for record in listed:
        name = record['path']
        if Path(name).is_absolute() or '..' in Path(name).parts or name not in entries:
            raise ValueError('Unexpected overlay path: ' + name)
        source = overlays / name
        if source.is_symlink():
            raise ValueError('Symlink in course overlay')
        content = source.read_bytes()
        content.decode('utf-8')
        if len(content) != record['bytes'] or digest(content) != record['sha256']:
            raise ValueError('Course overlay digest mismatch: ' + name)
        entries[name] = content
    manifest = verify_manifest(entries)
    if manifest['software_version'] != '1.5.4' or manifest['analysis_version'] != '1.1':
        raise ValueError('Unexpected course/scientific version')
    if any(digest(entries[name]) != value for name, value in protected.items()):
        raise ValueError('Protected scientific input, code or output changed')
    args.out.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(args.out, 'w', compression=zipfile.ZIP_STORED) as z:
        for name, content in sorted(entries.items()):
            info = zipfile.ZipInfo(PREFIX + name, date_time=STAMP)
            info.create_system = 3
            info.external_attr = 0o100644 << 16
            z.writestr(info, content)
    output = args.out.read_bytes()
    if len(output) != spec['course_zip_bytes'] or digest(output) != spec['course_zip_sha256']:
        raise ValueError('Reconstructed course ZIP differs from the tested archive')
    print(json.dumps({'status': 'passed', 'course_zip_sha256': digest(output),
                      'bytes': len(output), 'files': len(entries),
                      'overlay_files': len(listed), 'protected_files_unchanged': len(protected)}))


if __name__ == '__main__':
    main()
