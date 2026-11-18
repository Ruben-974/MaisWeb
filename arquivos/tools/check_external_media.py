"""Mapeia e confere as fontes externas, sem alterar as cópias locais."""
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from io import BytesIO
from pathlib import Path
from urllib.parse import urlsplit
import json
import requests
from PIL import Image, ImageOps

SUPPORT = Path(__file__).resolve().parents[1]
ROOT = SUPPORT.parent
DATA = SUPPORT/'dados'
HEADERS = {'User-Agent': 'Mozilla/5.0', 'Referer': 'https://www.aaci.org.br/'}


def image_url(asset):
    url = asset.get('url', '').replace('http://static.wixstatic.com/', 'https://static.wixstatic.com/')
    if not asset.get('crop') or not url:
        return url
    # Mantém o recorte editorial usando a transformação da própria CDN Wix.
    raw = url.split('/v1/')[0]
    response = requests.get(raw, headers=HEADERS, timeout=20)
    response.raise_for_status()
    with Image.open(BytesIO(response.content)) as original:
        ow, oh = ImageOps.exif_transpose(original).size
    with Image.open(SUPPORT/asset['source_path']) as captured:
        sw, sh = ImageOps.exif_transpose(captured).size
    scale = max(sw/ow, sh/oh)
    ox, oy = (ow-sw/scale)/2, (oh-sh/scale)/2
    left, top, right, bottom = asset['crop']
    x, y = round(ox+left/scale), round(oy+top/scale)
    width, height = round((right-left)/scale), round((bottom-top)/scale)
    name = urlsplit(raw).path.rsplit('/', 1)[-1]
    return f'{raw}/v1/crop/x_{x},y_{y},w_{width},h_{height}/fill/w_{asset["width"]},h_{asset["height"]},al_c,q_85,enc_auto/{name}'


def check(item):
    local, entry = item
    try:
        with requests.get(entry['url'], headers={**HEADERS, 'Range': 'bytes=0-1023'}, timeout=18, stream=True) as response:
            first = next(response.iter_content(chunk_size=512), b'')
            content_type = response.headers.get('Content-Type', '').split(';')[0]
            valid = response.status_code in (200, 206)
            valid = valid and (content_type.startswith('image/') if entry['tipo'] == 'imagem'
                              else first.startswith(b'%PDF') if entry['tipo'] == 'documento'
                              else content_type.startswith('video/'))
            entry.update(status=response.status_code, content_type=content_type, disponivel=valid)
    except requests.RequestException as error:
        entry.update(status=None, disponivel=False, erro=type(error).__name__)
    return local, entry


def main():
    assets = json.loads((DATA/'asset-map.json').read_text(encoding='utf-8'))
    docs = json.loads((DATA/'document-map.json').read_text(encoding='utf-8'))['documentos']
    resources = {}
    for asset in [*assets['imagens'].values(), *assets['parceiros'], *assets['galeria'], *assets['youtube'].values()]:
        local = asset['path']
        if local not in resources and asset.get('url') and (ROOT/local).is_file():
            resources[local] = {'url': image_url(asset), 'tipo': 'imagem'}
    resources['assets/img/logo.png'] = {'url': assets['logo']['url'], 'tipo': 'imagem'}
    for doc in docs:
        resources[doc['path']] = {'url': doc['url'], 'tipo': 'documento'}
    covers = {'VID-001': 'noticia-cozinha', 'VID-002': 'noticia-moveis', 'VID-003': 'noticia-mensagem', 'VID-004': 'noticia-doacao'}
    for key, video in assets['videos'].items():
        resources[video['path']] = {'url': video['url'], 'tipo': 'video'}
        resources[video['poster']] = {'url': image_url(assets['imagens'][covers[key]]), 'tipo': 'imagem'}
    with ThreadPoolExecutor(max_workers=8) as executor:
        resources = dict(executor.map(check, resources.items()))
    result = {'preferencia': 'externo', 'verificado_em': datetime.now(timezone.utc).isoformat(),
              'recursos': resources, 'sem_fonte_externa': ['assets/img/banner.webp', 'assets/img/favicon.png']}
    (DATA/'external-media.json').write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
    print(f'Fontes verificadas: {len(resources)}; disponíveis: {sum(r["disponivel"] for r in resources.values())}.')
    for local, entry in resources.items():
        if not entry['disponivel']:
            print(f'Indisponível: {local} — {entry.get("status") or entry.get("erro")}')


if __name__ == '__main__':
    main()
