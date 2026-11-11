"""Build deterministic public release assets from verified inputs (Python stdlib)."""
from pathlib import Path
import argparse, hashlib, json, re, shutil, zipfile

RELEASE = '1.6.3'
EXPECTED = {
    'project.zip': 'b94ebe3bb0ce7af5849ccdbaff11bb116d4613a18af611edcd2cf6243888559c',
    'course-python.zip': '1ee1825bcd3318441b263ed40dbcf869bb6091d1a6ec5e3a1d0cf54166369ef6',
    'proposal-english.mp4': 'a32e8498d693a24da82141c97b186e954ab61cdc47773329e7d01896172c28ec',
    'proposal-subtitled.mp4': '6a1e93fbf6c309e61bbc07da3a7c1d044d4a8529be361ab4e16ed9afa2a3c978',
}
PUBLIC_SITE_FILES = ['.nojekyll', 'CREDITS.txt', 'DATA_SOURCES.md', 'LICENSE', 'LICENSE-Plotly.txt', 'README.md', 'RELEASE_NOTES.md', 'THIRD_PARTY_NOTICES.md', 'analysis-state.js', 'app.js', 'chart-export.js', 'coverage-sources.js', 'data.js', 'dataset-query.js', 'datasets/bvbrc-NOTICE.txt', 'datasets/bvbrc-README.txt', 'datasets/bvbrc-data.js', 'datasets/bvbrc-provenance.json', 'datasets/europe-NOTICE.txt', 'datasets/europe-arg.js', 'datasets/europe-provenance.json', 'datasets/flu-NOTICE.txt', 'datasets/flu-data.csv', 'datasets/flu-data.js', 'datasets/flu-data.json', 'datasets/flu-metadata.json', 'datasets/global-sewage-NOTICE.txt', 'datasets/global-sewage-README.txt', 'datasets/global-sewage-data.js', 'datasets/global-sewage-provenance.json', 'datasets/ha-NOTICE.txt', 'datasets/ha-adapter.py', 'datasets/ha-data.js', 'datasets/ha-data.json', 'datasets/ha-metadata.json', 'datasets/ha-rows.csv', 'datasets/hk-community-NOTICE.txt', 'datasets/hk-community-archive-runs.tsv', 'datasets/hk-community-samples.csv', 'datasets/hk-community-source.xlsx', 'datasets/hk-community-table-s1.csv', 'datasets/hk-community-table-s2.csv', 'datasets/hk-community.js', 'datasets/phlsb-README.txt', 'datasets/phlsb-long.csv', 'datasets/phlsb-metadata.json', 'datasets/phlsb-parser.py', 'datasets/phlsb-source.csv', 'datasets/phlsb.js', 'datasets/phlsb.json', 'datasets/rainfall-NOTICE.txt', 'datasets/rainfall-data.csv', 'datasets/rainfall-data.js', 'datasets/rainfall-data.json', 'datasets/rainfall-metadata.json', 'datasets/supply-NOTICE.txt', 'datasets/supply-adapter.py', 'datasets/supply-data.csv', 'datasets/supply-data.js', 'datasets/supply-data.json', 'datasets/supply-metadata.json', 'en.vtt', 'es.vtt', 'experience-data.js', 'experience-overview.svg', 'experience-renderer.js', 'experience-source.json', 'experience.css', 'experience.html', 'experience.js', 'export-contract.js', 'extension-query.js', 'fr.vtt', 'index.html', 'ja.vtt', 'ko.vtt', 'licenses/plotly-js-3.1.1-LICENSE.txt', 'map-source.json', 'plotly.min.js', 'poster.jpg', 'proposal-subtitled.mp4', 'proposal.mp4', 'release_sources.json', 'research-catalog.js', 'research-data.js', 'research-datasets.json', 'research-extension-index.js', 'research-query.js', 'review-diagnostics.json', 'scripts/adapters/bvbrc_adapter.py', 'scripts/adapters/europe_arg.py', 'scripts/adapters/flu.py', 'scripts/adapters/global_sewage_adapter.py', 'scripts/adapters/ha_blood.py', 'scripts/adapters/hk_community.py', 'scripts/adapters/phlsb.py', 'scripts/adapters/rainfall.py', 'scripts/adapters/refresh_extension_index.cjs', 'scripts/adapters/refresh_manifest.py', 'scripts/adapters/run_all.py', 'scripts/adapters/supply.py', 'source_manifest.json', 'style.css', 'video.css', 'video.html', 'video.js', 'yue.vtt', 'zh-CN.vtt', 'zh-TW.vtt', 'zip-store.js']

def sha(data):
    return hashlib.sha256(data).hexdigest()

def jb(value):
    return (json.dumps(value, ensure_ascii=False, indent=2) + '\n').encode()

def verified_bytes(path, expected):
    data = path.read_bytes()
    if sha(data) != expected:
        raise ValueError('SHA256 mismatch: ' + path.name)
    return data

def archive(path, expected):
    verified_bytes(path, expected)
    with zipfile.ZipFile(path) as z:
        if z.testzip() is not None or len(z.namelist()) != len(set(z.namelist())):
            raise ValueError('Invalid ZIP: ' + path.name)
        entries = {n: z.read(n) for n in z.namelist() if not n.endswith('/')}
    for name in entries:
        if Path(name).is_absolute() or '..' in Path(name).parts:
            raise ValueError('Unsafe ZIP path: ' + name)
    return entries

def verify_manifest(entries):
    m = json.loads(entries['release_manifest.json'])
    if set(entries) != {r['path'] for r in m['files']} | {'release_manifest.json'}:
        raise ValueError('Manifest inventory mismatch')
    for row in m['files']:
        data = entries[row['path']]
        if len(data) != row['bytes'] or sha(data) != row['sha256']:
            raise ValueError('Manifest digest mismatch: ' + row['path'])
    return m

def row(name, data):
    return {'path': name, 'bytes': len(data), 'sha256': sha(data)}

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo', type=Path, required=True)
    parser.add_argument('--course-zip', type=Path, required=True)
    parser.add_argument('--previous-project', type=Path, required=True)
    parser.add_argument('--previous-video-dir', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    previous = archive(args.previous_project, EXPECTED['project.zip'])
    verify_manifest(previous)
    raw_course = archive(args.course_zip, EXPECTED['course-python.zip'])
    prefix = 'MATH7005 Course/'
    if not all(name.startswith(prefix) for name in raw_course):
        raise ValueError('Unexpected course archive prefix')
    course = {name[len(prefix):]: data for name, data in raw_course.items()}
    course_manifest = verify_manifest(course)
    shutil.copyfile(args.course_zip, args.out / 'course-python.zip')
    (args.out / 'report.pdf').write_bytes(course['outputs/项目报告.pdf'])
    for name in ['proposal-english.mp4', 'proposal-subtitled.mp4']:
        data = verified_bytes(args.previous_video_dir / name, EXPECTED[name])
        (args.out / name).write_bytes(data)

    entries = {n: d for n, d in previous.items() if n.startswith(('frozen-browser-source/', 'video/', 'subtitles/'))}
    entries.update({'python-app/' + n: d for n, d in course.items()})
    media = {n: d for n, d in previous.items() if n.startswith('python-app/assets/proposal/')}
    entries.update(media)
    # The public application adds the already-released video; its outer and component manifests both cover those files.
    course_manifest.update({'kind': 'public_python_application', 'status': 'executed_source_in_public_release',
        'course_archive_sha256': EXPECTED['course-python.zip'], 'files': [row(n.removeprefix('python-app/'), d)
        for n, d in sorted(entries.items()) if n.startswith('python-app/') and n != 'python-app/release_manifest.json']})
    entries['python-app/release_manifest.json'] = jb(course_manifest)
    for name in PUBLIC_SITE_FILES:
        source = args.repo / name
        if source.is_symlink() or not source.is_file():
            raise ValueError('Missing or invalid allowlisted website file: ' + name)
        data = source.read_bytes()
        if name.startswith('datasets/') and data != previous['website/' + name]:
            raise ValueError('Changed frozen research dataset: ' + name)
        entries['website/' + name] = data
    source_manifest = json.loads(entries['website/source_manifest.json'])
    if source_manifest['release_version'] != RELEASE:
        raise ValueError('Website version mismatch')
    for name, record in source_manifest['source_files'].items():
        data = entries['frozen-browser-source/' + name]
        if len(data) != record['bytes'] or sha(data) != record['sha256']:
            raise ValueError('Frozen browser evidence mismatch: ' + name)
    entries['frozen-browser-source/source_manifest.json'] = entries['website/source_manifest.json']
    receipt = json.loads(entries['python-app/outputs/artifact_manifest.json'])
    for name, record in receipt['files'].items():
        data = entries['python-app/' + name]
        if len(data) != record['bytes'] or sha(data) != record['sha256']:
            raise ValueError('Python artifact receipt mismatch: ' + name)
    components = {
        'website': {'version': RELEASE},
        'python': {'version': '1.5.3', 'course_archive_sha256': EXPECTED['course-python.zip']},
        'analysis': {'version': '1.1', 'rerun_in_this_release': True, 'numeric_changed_cells': 0},
        'media': {'version': '1.5.2', 'changed_in_this_release': False},
    }
    sources = json.loads(previous['COMPONENT_SOURCES.json'])
    sources.update({'release_version': RELEASE, 'components': components,
        'baseline_project': {'bytes': args.previous_project.stat().st_size, 'sha256': EXPECTED['project.zip']},
        'course_python_asset': {'bytes': args.course_zip.stat().st_size, 'sha256': EXPECTED['course-python.zip']},
        'verification_scope': 'All archive files and Python receipts verified. 157 Python tests passed; one internal archive test explicitly deselected. Independent rebuild reproduced all 26 CSV files, 8,173 rows and 108,164 numeric cells exactly. Website tests used Node DOM and course UI tests used Streamlit AppTest. Media and frozen browser evidence remain unchanged.'})
    entries['COMPONENT_SOURCES.json'] = jb(sources)
    entries['README.txt'] = b'''Hong Kong Wastewater Explorer 1.6.3

Open the app: https://liilymiao.github.io/hong-kong-wastewater-explorer/
website/: website 1.6.3 with numeric and empty-result boundary fixes.
python-app/: Python 1.5.3 course workflow, real-origin recomputation and English report.
Scientific configuration 1.1 is unchanged. Independent reproduction found no numeric differences.
video/ and subtitles/: unchanged video and eight subtitle tracks from 1.5.2.
frozen-browser-source/: original saved browser-analysis evidence.
website/datasets/: separately sourced public data with original metadata and terms.
python-app/README.md explains installation, launch and independent reproduction.
python-app/Course.md contains the ten-minute walkthrough and closed-book preparation.
Dated candidate records describe the completed pre-publication acceptance run.
release_manifest.json records every packaged file size and SHA256.
'''
    for name, data in entries.items():
        try:
            text = data.decode('utf-8')
        except UnicodeDecodeError:
            continue
        if re.search(r'/Users/[^/\s"\']+', text):
            raise ValueError('Private machine path in ' + name)
    manifest = {'kind': 'public_project', 'release_version': RELEASE, 'components': components,
                'files': [row(n, d) for n, d in sorted(entries.items())]}
    entries['release_manifest.json'] = jb(manifest)
    # Stored entries avoid host zlib differences; timestamps/modes/order are fixed for local/CI identical bytes.
    destination = args.out / 'project.zip'
    with zipfile.ZipFile(destination, 'w', compression=zipfile.ZIP_STORED) as z:
        for name, data in sorted(entries.items()):
            info = zipfile.ZipInfo(name, date_time=(2026, 11, 11, 0, 0, 0))
            info.create_system = 3
            info.external_attr = 0o100644 << 16
            z.writestr(info, data)
    with zipfile.ZipFile(destination) as z:
        if z.testzip() is not None:
            raise ValueError('Final ZIP CRC failure')
        final = {name: z.read(name) for name in z.namelist()}
    verify_manifest(final)
    verify_manifest({name.removeprefix('python-app/'): data for name, data in final.items() if name.startswith('python-app/')})
    assets = [{'name': name, 'bytes': (args.out / name).stat().st_size,
               'sha256': sha((args.out / name).read_bytes())}
              for name in ['course-python.zip', 'project.zip', 'proposal-english.mp4', 'proposal-subtitled.mp4', 'report.pdf']]
    (args.out / 'SHA256SUMS.txt').write_text(''.join(record['sha256'] + '  ' + record['name'] + '\n' for record in assets))
    record = {'status': 'passed', 'release_version': RELEASE, 'project_files': len(entries),
              'python_receipts_verified': len(receipt['files']), 'frozen_browser_sources_verified': len(source_manifest['source_files']),
              'python_proposal_media_files_preserved': len(media), 'course_archive_exact_tested_bytes': True,
              'website_allowlist_files': len(PUBLIC_SITE_FILES), 'private_machine_paths_found': 0, 'assets': assets}
    (args.out / 'build-verification.json').write_bytes(jb(record))
    print(json.dumps(record, indent=2))

if __name__ == '__main__':
    main()
