#!/usr/bin/env python3
"""RoutineFit 1.7.4: original exercise artwork in batches of 10, review-only.

Never changes the user's workout data, main app, or Android package.
Each image has an independently generated prompt and a stable exercise-ID filename.
"""
import argparse
import base64
import hashlib
import io
import json
import os
import re
from pathlib import Path
import sys
import time
import urllib.error
import urllib.request


ROOT = Path(__file__).resolve().parents[2]
CATALOG = ROOT / 'automation/rf174/catalog.json'
OUT = ROOT / 'media/rf174-review'
STATE = OUT / 'progress.json'
DEFAULT_MODEL = 'gpt-image-1-mini'


def load_json(path, default):
    return json.loads(path.read_text(encoding='utf-8')) if path.exists() else default


def atomic_write(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + '.tmp')
    temporary.write_bytes(data)
    temporary.replace(path)


def prompt_for(ex):
    # Do not use, download, or modify third-party copyrighted exercise images.
    return (
        'Create a NEW, ORIGINAL, scientifically plausible exercise pose illustration for a Korean fitness app. '
        'The exercise is EXACTLY: ' + ex['name'] + '. '
        'Target muscle group: ' + ex.get('muscle', '전신') + '. '
        'Equipment type: ' + ex.get('equipment', 'body') + '. '
        'Exercise description: ' + ex.get('description', '') + '. '
        'Movement and safety cues: ' + ex.get('tip', '') + '. '
        'Show a single athletic adult demonstrating a recognizable middle phase of the SPECIFIC named exercise, '
        'with the CORRECT grip, limb positions, machine, cable direction, bench angle, weight placement and anatomical movement. '
        'A precise 3/4-angle, full-body view with equipment visible and anatomically correct joints. '
        'Neutral-gender non-identifiable anatomy mannequin, modest opaque sportswear, non-sexual, clinical educational style. '
        'Semi-realistic 3D anatomical fitness illustration; softly highlight the actively working muscles as translucent red overlays '
        'over normal athletic clothing where appropriate, without exposing intimate anatomy. '
        'Dark blue-gray minimal studio background, subtle green rim light, consistent professional illustration style. '
        'Only one view of one pose, no duplicate or mirrored person, no text, no labels, no watermark, no brand logos. '
        'DO NOT output a generic standing exercise pose. Do not copy existing images. '
        'Prioritize accurate exercise biomechanics over decorative style.'
    )


def generate_image(ex, model, token):
    body = json.dumps({
        'model': model, 'prompt': prompt_for(ex), 'n': 1,
        'size': '1024x1024', 'quality': 'medium', 'output_format': 'webp'
    }).encode('utf-8')
    request = urllib.request.Request(
        'https://api.openai.com/v1/images/generations', data=body,
        headers={'Authorization': 'Bearer ' + token, 'Content-Type': 'application/json'}, method='POST')
    for attempt in range(3):
        try:
            with urllib.request.urlopen(request, timeout=240) as response:
                obj = json.load(response)
            encoded = obj['data'][0]['b64_json']
            return base64.b64decode(encoded, validate=True)
        except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError) as err:
            status = getattr(err, 'code', None)
            if attempt < 2 and (status in (408, 409, 429, 500, 502, 503, 504) or status is None):
                print(f'Retryable image API failure for {ex["id"]} ({status or "network"}), attempt {attempt+1}', file=sys.stderr)
                time.sleep(4 * (attempt + 1))
                continue
            raise RuntimeError(f'Image API failed on {ex["id"]}; HTTP {status or "network"}. No key disclosed.') from None


def validate_webp(data):
    from PIL import Image
    if len(data) < 10000:
        raise ValueError('Output too small to be a suitable exercise illustration')
    image = Image.open(io.BytesIO(data))
    image.verify()
    image = Image.open(io.BytesIO(data))
    if image.format != 'WEBP' or image.width < 512 or image.height < 512:
        raise ValueError('Image must be WebP with at least 512x512 resolution')
    return image.width, image.height


def write_gallery(catalog, state, new_ids):
    from PIL import Image, ImageDraw
    by_id = {ex['id']: ex for ex in catalog}
    entries = list(state['images'])
    cards = []
    for ex_id in entries:
        ex = by_id.get(ex_id)
        if not ex:
            continue
        safe_name = (ex['name'].replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
                     .replace('"', '&quot;').replace("'", '&#39;'))
        cards.append(f'<figure><img loading="lazy" src="./{ex_id}.webp" alt="{safe_name}"><figcaption>{safe_name} <small>{ex_id}</small></figcaption></figure>')
    html = ('<!doctype html><html lang="ko"><meta charset="utf-8"><meta name="viewport" content="width=device-width">'
            '<title>RoutineFit 1.7.4 이미지 검수</title><style>body{background:#101e29;color:#e9f5f5;font-family:sans-serif;margin:20px}'
            'section{display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:18px}'
            'figure{margin:0;background:#1a2d37;border-radius:15px;overflow:hidden}img{width:100%;display:block}'
            'figcaption{padding:10px;font-weight:700}small{display:block;color:#a8bec9;font-weight:400;margin-top:5px}</style>'
            '<h1>RoutineFit 1.7.4 운동 이미지 검수</h1><p>자동 이미지 기술 검증만 통과한 미승인 이미지입니다. 자세·장비·동작은 사람의 검수가 필요합니다.</p>'
            '<section>' + ''.join(cards) + '</section></html>')
    atomic_write(OUT / 'gallery.html', html.encode('utf-8'))
    atomic_write(OUT / 'latest-batch.json', json.dumps({'new_ids': new_ids, 'generated_total': len(entries)}, ensure_ascii=False, indent=2).encode('utf-8'))
    if new_ids:
        w, h = 230, 262
        sheet = Image.new('RGB', (w * 5, h * 2), '#172630')
        draw = ImageDraw.Draw(sheet)
        for i, ex_id in enumerate(new_ids[:10]):
            pic = Image.open(OUT / (ex_id + '.webp')).convert('RGB')
            pic.thumbnail((w-12, h-34))
            col, row = i % 5, i // 5
            x, y = col*w+6, row*h+6
            sheet.paste(pic, (x, y))
            draw.text((x, row*h + h - 20), ex_id[:27], fill='#ffffff')
        sheet.save(OUT / 'latest-contact-sheet.webp', 'WEBP', quality=82)


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--mode', choices=['audit', 'generate'], default='audit')
    p.add_argument('--batch-size', type=int, default=10)
    args = p.parse_args()
    if not 1 <= args.batch_size <= 10:
        p.error('batch-size must be from 1 to 10')
    catalog_data = load_json(CATALOG, None)
    if not isinstance(catalog_data, dict) or not isinstance(catalog_data.get('exercises'), list):
        raise RuntimeError('Missing or invalid automation/rf174/catalog.json')
    catalog = catalog_data['exercises']
    if len(catalog) != 645 or len(set(x['id'] for x in catalog)) != len(catalog) or any(not re.fullmatch(r'[A-Za-z0-9_-]{1,90}', x['id']) for x in catalog):
        raise RuntimeError(f'Catalog consistency error: need 645 unique IDs; actual {len(catalog)}')
    progress = load_json(STATE, {'images': {}})
    progress.setdefault('images', {})
    if not isinstance(progress['images'], dict):
        raise RuntimeError('Corrupt progress.json: images must be a map')
    for ex_id in list(progress['images']):
        if not (OUT / (ex_id + '.webp')).is_file():
            raise RuntimeError(f'Progress refers to missing file: {ex_id}')
    pending = [ex for ex in catalog if ex['id'] not in progress['images']]
    print(f'Catalog: {len(catalog)} / done: {len(progress["images"])} / remaining: {len(pending)}')
    print('Next batch: ' + ', '.join(ex['name'] for ex in pending[:args.batch_size]))
    if args.mode == 'audit':
        return
    token = os.environ.get('OPENAI_API_KEY', '')
    if not token:
        raise RuntimeError('OPENAI_API_KEY secret is missing. Set it in GitHub Settings > Secrets and variables > Actions.')
    model = os.environ.get('RF174_IMAGE_MODEL', DEFAULT_MODEL)
    if model not in ('gpt-image-1-mini', 'gpt-image-1.5', 'gpt-image-2', 'gpt-image-2.5-flare', 'gpt-image-2.5-sunburst'):
        raise RuntimeError('Unrecognized model, refusing automatic paid generation')
    new_ids = []
    for ex in pending[:args.batch_size]:
        try:
            image_bytes = generate_image(ex, model, token)
            width, height = validate_webp(image_bytes)
        except (RuntimeError, ValueError) as err:
            if not new_ids:
                raise
            print('Batch interrupted; committing completed images. Next run retries missing image: ' + str(err), file=sys.stderr)
            break
        ex_id = ex['id']
        atomic_write(OUT / (ex_id + '.webp'), image_bytes)
        progress['images'][ex_id] = {
            'name': ex['name'], 'model': model, 'size': [width, height],
            'sha256': hashlib.sha256(image_bytes).hexdigest(),
            'prompt_sha256': hashlib.sha256(prompt_for(ex).encode('utf-8')).hexdigest(),
            'review': 'needs-human-review'
        }
        atomic_write(STATE, json.dumps(progress, ensure_ascii=False, indent=2).encode('utf-8'))
        new_ids.append(ex_id)
        print(f'New image {len(new_ids)}/{min(args.batch_size, len(pending))}: {ex["name"]} ({ex_id})')
    write_gallery(catalog, progress, new_ids)
    print(f'Generated this run: {len(new_ids)}; total: {len(progress["images"])} / {len(catalog)}; published to app: 0')


if __name__ == '__main__':
    main()
