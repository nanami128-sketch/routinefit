"""Verify exact exercise routes, release identity, file hashes, and APK assets."""
import argparse, hashlib, json, re, zipfile
from pathlib import Path

p=argparse.ArgumentParser()
p.add_argument('--root', default='.')
p.add_argument('--apk')
a=p.parse_args()
root=Path(a.root)
manifest=json.loads((root/'automation/rf174/complete644_manifest.json').read_text())
assert manifest['count']==644 and manifest['version']=='1.7.4.4'
rows=manifest['images']
assert len(rows)==644 and len({e['id'] for e in rows})==644
def check(read):
    html=read('index.html').decode()
    assert "VERSION='1.7.4.4'" in html and "STORE_KEY='routinefit_v1_store'" in html
    mapping={}
    for line in html.splitlines():
        if line.startswith(('const RF_V174_EXACT_BY_ID=','Object.assign(RF_V174_EXACT_BY_ID,')):
            mapping.update(json.loads(line[line.index('{'):line.rindex('}')+1]))
    assert len(mapping)==644
    sw=read('sw.js').decode()
    core=json.loads(re.search(r'const CORE\s*=\s*(\[[^;]+\]);',sw).group(1))
    assert 'routinefit-complete644-1.7.4.4-' in sw
    hashes=set()
    for e in rows:
        assert mapping[e['id']]==e['path']
        assert './'+e['path'] in core
        data=read(e['path'])
        sha=hashlib.sha256(data).hexdigest()
        assert sha==e['sha256'] and sha not in hashes,e['id']
        hashes.add(sha)
        assert min(e['width'],e['height'])>=1024
        assert data[:4]==b'RIFF' and data[8:12]==b'WEBP'
    return hashlib.sha256(read('index.html')).hexdigest()
expected=check(lambda f:(root/f).read_bytes())
gradle=(root/'android/app/build.gradle').read_text()
assert "applicationId 'com.nanami128sketch.routinefit'" in gradle
assert 'versionCode 177' in gradle and "versionName '1.7.4.4'" in gradle
if a.apk:
    with zipfile.ZipFile(a.apk) as z:
        assert z.testzip() is None
        assert check(lambda f:z.read('assets/'+f))==expected
    print('PASS: release APK contains all 644 reviewed images and exact validated app HTML')
else:
    print('PASS: 644 unique image routes, SHA256, native-size metadata, offline cache, app ID and version 177')
