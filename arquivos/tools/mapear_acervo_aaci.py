"""Inventaria e organiza a captura local da AACI sem alterar o espelho HTTrack."""
from __future__ import annotations

import csv
import hashlib
import html as escape_html
import io
import json
import mimetypes
import os
import re
import shutil
import subprocess
import sys
import unicodedata
import zipfile
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from urllib.parse import unquote, urljoin, urlsplit

from lxml import html
from PIL import Image, ImageDraw, ImageFont, ImageOps

WORKSPACE = Path(__file__).resolve().parents[1]
SOURCE = WORKSPACE / "mapeamento site" / "AACI"
DEST = WORKSPACE / "mapeamento site" / "AACI-organizado"
TMP = WORKSPACE / "tmp" / "aaci-mapeamento"
sys.path.insert(0, str(Path(os.environ.get("TEMP", "/tmp")) / "aaci-pdf-tools"))
import pymupdf as fitz

NOW = "13/11/2026"
IMG_EXT = {".jpg", ".jpeg", ".png", ".gif", ".webp", ".avif", ".svg", ".bmp"}
FONT_EXT = {".ttf", ".otf", ".woff", ".woff2"}
IGNORE_TEXT = {"To play, press and hold the enter key. To stop, release the enter key.", "top of page", "bottom of page"}
PUBLIC_TOPICS = {
    "institucional": ["quem-somos", "index", "nossaequipe", "parceiros", "nossas-instala"],
    "servicos-e-projetos": ["servico", "apadrinhamento", "2024"],
    "doacoes-e-participacao": ["comoajudar", "volunt", "telemarketing"],
    "transparencia": ["transpar", "presta"],
    "noticias-e-midias": ["blog", "post/", "galeria", "video", "foto"],
    "contato-e-privacidade": ["contato", "privacidade"],
    "trabalho-e-colaboradores": ["trabalhe", "colaboradores"],
}


def norm(value):
    return unicodedata.normalize("NFKD", str(value)).encode("ascii", "ignore").decode().lower()


def slug(value, limit=90):
    return re.sub(r"[^a-z0-9]+", "-", norm(unquote(value))).strip("-")[:limit].rstrip("-") or "arquivo"


def tidy(value):
    return " ".join(str(value).replace("\u200b", "").replace("\ufeff", "").split())


def decode_path(value):
    for _ in range(5):
        decoded = unquote(value)
        if decoded == value: break
        value = decoded
    return value


def dump(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")


def write_csv(path, rows, fields):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields, delimiter=";", extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({k: json.dumps(v, ensure_ascii=False) if isinstance(v, (list, dict)) else v for k, v in row.items()})


def topic_for(path):
    value = norm(path)
    if value.startswith('post/') or re.fullmatch(r'20\d{2}\.html', value):
        return 'noticias-e-midias'
    for topic, needles in PUBLIC_TOPICS.items():
        if any(norm(n) in value for n in needles):
            return topic
    return "outras-paginas"


def media_family(value):
    match = re.search(r"(?:static\.wixstatic\.com/)?media/([^/\s?]+)", unquote(value), re.I)
    if match:
        return match.group(1).replace("_mv2", "~mv2")
    match = re.search(r"i\.ytimg\.com/vi(?:_webp)?/([^/]+)", value)
    return "youtube-" + match.group(1) if match else ""


def short_url(value):
    return value.replace("\\/", "/").replace("&amp;", "&").strip("'\" ,;)")


def relative_href(source_page, target):
    return Path(os.path.relpath(target, source_page.parent)).as_posix()


def html_text(node):
    clone = html.fromstring(html.tostring(node, encoding="unicode"))
    for el in clone.xpath(".//script|.//style|.//noscript|.//svg|.//template"):
        el.drop_tree()
    return [tidy(t) for t in clone.xpath(".//text()") if tidy(t) and tidy(t) not in IGNORE_TEXT]


def safe_title(raw, fallback):
    clean = re.sub(r"\s*\|\s*Aaci(?:jf)?\s*$", "", raw, flags=re.I)
    return tidy(clean or fallback)


def load_capture():
    files = sorted((p for p in SOURCE.rglob("*") if p.is_file()), key=lambda p: p.as_posix().lower())
    records = []
    for index, path in enumerate(files, 1):
        data = path.read_bytes()
        stat = path.stat()
        records.append({"id": f"ARQ-{index:04}", "origem": path.relative_to(SOURCE).as_posix(),
                        "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest(),
                        "mtime_ns": stat.st_mtime_ns, "extensao_original": path.suffix.lower(),
                        "tipo": "", "organizado": "", "paginas": [], "rotulos": [], "urls": [],
                        "status": "lido", "_path": path})
    return records


def parse_httrack(records):
    by_normal = {decode_path(r["origem"]): r for r in records}
    transfers = []
    for line in (SOURCE / "hts-cache/new.txt").read_text(encoding="utf-8", errors="replace").splitlines()[1:]:
        cols = line.split("\t")
        if len(cols) < 9:
            continue
        origin = cols[7]
        local = cols[8].split("/AACI/", 1)[-1] if "/AACI/" in cols[8] else ""
        transfer = {"url": origin, "status_http": cols[3], "mime": cols[5], "caminho_cache": local,
                    "pagina_referente": cols[9][6:-1] if len(cols) > 9 else "", "tamanho": cols[1]}
        transfers.append(transfer)
        rec = by_normal.get(decode_path(local))
        if rec:
            rec["urls"].append(origin)
            rec["mime_httrack"] = cols[5]
            rec["status_http"] = cols[3]
            rec["origem_captura"] = transfer["pagina_referente"]
    return transfers


def classify(records):
    image_num = doc_num = video_num = 0
    for rec in records:
        path, ext = rec["_path"], rec["extensao_original"]
        if ext in IMG_EXT:
            image_num += 1
            rec["tipo"] = "imagem"
            rec["asset_id"] = f"IMG-{image_num:04}"
            rec["familia"] = media_family(rec["urls"][0] if rec["urls"] else rec["origem"]) or rec["sha256"]
            try:
                with Image.open(path) as im:
                    rec.update({"largura": im.width, "altura": im.height, "formato_real": im.format,
                                "modo": im.mode, "quadros": getattr(im, "n_frames", 1)})
                    im.verify()
                rec["mime_real"] = Image.MIME.get(rec["formato_real"], "image/unknown")
            except Exception as exc:
                if ext == ".svg":
                    rec["formato_real"] = "SVG"
                else:
                    rec["status"] = "erro_leitura_imagem"
                    rec["erro"] = str(exc)
        elif ext == ".pdf":
            doc_num += 1
            rec["tipo"] = "documento"
            rec["asset_id"] = f"DOC-{doc_num:03}"
        elif ext in {".mp4", ".webm", ".mov", ".m4v", ".mp3", ".wav"}:
            video_num += 1
            rec["tipo"] = "video" if ext not in {".mp3", ".wav"} else "audio"
            rec["asset_id"] = f"VID-{video_num:03}"
        elif ext == ".html": rec["tipo"] = "html"
        elif ext in FONT_EXT: rec["tipo"] = "fonte"
        elif ext == ".js": rec["tipo"] = "javascript"
        elif ext == ".css": rec["tipo"] = "css"
        elif "hts-cache/" in rec["origem"] or path.name in {"hts-log.txt", "cookies.txt"}: rec["tipo"] = "httrack"
        else: rec["tipo"] = "auxiliar"
    return records


def analyze_pages(records):
    local_by_norm = {decode_path(r["origem"]): r for r in records}
    url_lookup = {decode_path(u): r for r in records for u in r["urls"]}
    family_lookup = defaultdict(list)
    for rec in records:
        if rec.get("familia"): family_lookup[rec["familia"]].append(rec)
    pages, all_links, structured_videos, media_context = [], [], {}, defaultdict(list)

    def resolve(raw, file):
        raw = short_url(raw)
        if not raw or raw.startswith(("#", "data:", "javascript:", "mailto:", "tel:")): return None
        if raw.startswith(("http:", "https:")):
            return url_lookup.get(decode_path(raw))
        candidate = (file.parent / raw.split("?", 1)[0].split("#", 1)[0]).resolve()
        try: rel = candidate.relative_to(SOURCE).as_posix()
        except ValueError: return None
        return local_by_norm.get(decode_path(rel))

    def walk_json(obj, parent_label="", page_id="", depth=0):
        if depth > 32: return
        if isinstance(obj, str):
            if len(obj) > 20 and obj.lstrip().startswith(("{", "[")):
                try: walk_json(json.loads(obj), parent_label, page_id, depth + 1)
                except (ValueError, RecursionError): pass
            return
        if isinstance(obj, list):
            for child in obj: walk_json(child, parent_label, page_id, depth + 1)
        elif isinstance(obj, dict):
            label = obj.get("headline") or obj.get("title") or obj.get("name") or parent_label
            if not isinstance(label, str): label = parent_label
            if obj.get("@type") == "VideoObject":
                link = obj.get("contentUrl") or obj.get("embedUrl") or ""
                key = link or label
                item = structured_videos.setdefault(key, {"titulo": label, "url": link, "descricao": obj.get("description", ""),
                    "duracao_declarada": obj.get("duration", ""), "data_publicacao": obj.get("uploadDate", ""),
                    "thumbnail": obj.get("thumbnailUrl", ""), "paginas": []})
                if page_id not in item["paginas"]: item["paginas"].append(page_id)
            if label and len(label) < 250 and label != parent_label:
                serialized = json.dumps(obj, ensure_ascii=False)
                for match in set(re.findall(r"c696b8_[a-f0-9]{32}(?=[/\"\\])", serialized)):
                    media_context[match].append({"titulo": tidy(label), "pagina": page_id, "peso": len(serialized)})
            for child in obj.values(): walk_json(child, label, page_id, depth + 1)

    for rec in [r for r in records if r["tipo"] == "html"]:
        raw = rec["_path"].read_text(encoding="utf-8", errors="replace")
        try: tree = html.fromstring(raw)
        except Exception:
            rec["tipo"] = "html-tecnico"; continue
        title = tidy(tree.xpath("string(//title)"))
        main = tree.xpath("//main")
        if not main or "www.aaci.org.br/" not in rec["origem"]:
            rec["tipo"] = "html-erro" if re.search(r"(?:400|404|403).*Erro|Bad Request|Not Found", title, re.I) else "html-tecnico"
            rec["titulo"] = title
            continue
        rec["tipo"] = "pagina"
        page_id = f"PAG-{len(pages)+1:03}"
        origin = rec["urls"][0] if rec["urls"] else ""
        mirror = re.search(r"Mirrored from (.*?) by HTTrack", raw)
        if mirror: origin = mirror.group(1)
        clean_lines = html_text(main[0])
        headings = list(dict.fromkeys(tidy(el.text_content()) for el in main[0].xpath(".//h1|.//h2|.//h3|.//h4") if tidy(el.text_content())))
        page = {"id": page_id, "arquivo_id": rec["id"], "titulo": safe_title(title, rec["_path"].stem),
                "url": origin, "origem": rec["origem"], "tema": topic_for(rec["origem"].split("/", 1)[-1]),
                "linhas": clean_lines, "texto": "\n".join(clean_lines), "titulos": headings,
                "imagens": [], "documentos": [], "videos_locais": [], "links": [], "formularios": []}
        page["caracteres_texto"] = len(page["texto"])
        page["status_conteudo"] = "texto_recuperado" if len(page["texto"]) > 100 else "conteudo_escasso_ou_dinamico"
        if title.startswith("Post |"):
            page["status_conteudo"] = "post_sem_conteudo_confirmado"
        for el in tree.xpath("//img"):
            alt = tidy(el.get("alt", ""))
            is_main = bool(el.xpath("ancestor::main"))
            urls = [el.get("src", ""), el.get("data-src", "")]
            urls += re.findall(r"(\S+)\s+\d+(?:\.\d+)?[wx]", el.get("srcset", ""))
            families = set()
            for u in urls:
                asset = resolve(u, rec["_path"])
                if asset:
                    if page_id not in asset["paginas"]: asset["paginas"].append(page_id)
                    if alt and alt not in asset["rotulos"]: asset["rotulos"].append(alt)
                    fam = asset.get("familia")
                    if fam: families.add(fam)
                    if is_main and asset["id"] not in page["imagens"]: page["imagens"].append(asset["id"])
            for fam in families:
                for asset in family_lookup[fam]:
                    if page_id not in asset["paginas"]: asset["paginas"].append(page_id)
                    if is_main:
                        asset.setdefault("paginas_conteudo", [])
                        if page_id not in asset["paginas_conteudo"]: asset["paginas_conteudo"].append(page_id)
                        if asset["id"] not in page["imagens"]: page["imagens"].append(asset["id"])
                    if alt and alt not in asset["rotulos"]: asset["rotulos"].append(alt)
        for a in main[0].xpath(".//a[@href]"):
            href = a.get("href", "").strip()
            label = tidy(a.text_content()) or tidy(" ".join(a.xpath(".//img/@alt")))
            target = resolve(href, rec["_path"])
            if href.startswith(("#", "javascript:")) or not href: continue
            url = (target["urls"][0] if target and target["urls"] else urljoin(origin, href)) if not href.startswith(("mailto:", "tel:")) else href
            link = {"pagina": page_id, "rotulo": label, "url": url, "href_capturado": href,
                    "arquivo_local_id": target["id"] if target else "", "presente_localmente": bool(target)}
            page["links"].append(link); all_links.append(link)
            if target:
                if page_id not in target["paginas"]: target["paginas"].append(page_id)
                if label and label not in target["rotulos"]: target["rotulos"].append(label)
                bucket = {"documento": "documentos", "video": "videos_locais"}.get(target["tipo"])
                if bucket and target["id"] not in page[bucket]: page[bucket].append(target["id"])
        for form in main[0].xpath(".//form"):
            fields = []
            for el in form.xpath(".//input|.//textarea|.//select"):
                if el.get("type") == "hidden": continue
                labels = form.xpath('.//label[@for=$field_id]', field_id=el.get('id',''))
                label = tidy(' '.join(x.text_content() for x in labels))
                fields.append({"tipo": el.get("type", el.tag), "nome": el.get("name", ""), "rotulo": el.get("aria-label") or el.get("placeholder") or label, "obrigatorio": "required" in el.attrib})
            page["formularios"].append({"campos": fields, "acao": form.get("action", ""), "estado": "estrutura_capturada_sem_backend_local"})
        for script in tree.xpath("//script[not(@src)]"):
            text = script.text or ""
            if text.lstrip().startswith(("{", "[")):
                try: walk_json(json.loads(text), page_id=page_id)
                except (ValueError, RecursionError): pass
        # Arquivos de mídia mencionados em dados estruturados de aplicativos Wix.
        for video in [r for r in records if r["tipo"] == "video"]:
            media_id = next((part for part in video["origem"].split("/") if re.fullmatch(r"c696b8_[a-f0-9]{32}", part)), "")
            if media_id and media_id in raw:
                if page_id not in video["paginas"]: video["paginas"].append(page_id)
                if video["id"] not in page["videos_locais"]: page["videos_locais"].append(video["id"])
        rec["pagina_id"] = page_id
        rec["titulo"] = page["titulo"]
        pages.append(page)
    for video in [r for r in records if r["tipo"] == "video"]:
        mid = next((p for p in video["origem"].split("/") if re.fullmatch(r"c696b8_[a-f0-9]{32}", p)), "")
        candidates = sorted(media_context.get(mid, []), key=lambda x: x["peso"])
        video["titulo"] = candidates[0]["titulo"] if candidates else "Vídeo AACI " + video["asset_id"]
        video["titulos_contextuais"] = list(dict.fromkeys(c["titulo"] for c in candidates))[:12]
    return pages, all_links, list(structured_videos.values()), resolve


def image_group(rec, page_map):
    label = norm(" ".join(rec["rotulos"]))
    topics = {page_map[p]["tema"] for p in rec.get("paginas_conteudo", []) if p in page_map}
    stems = " ".join(page_map[p]["origem"] for p in rec.get("paginas_conteudo", []) if p in page_map)
    if "i.ytimg.com/" in rec["origem"] or re.search(r"f00[0-9]\.jpg", rec["origem"]): return "miniaturas-de-videos"
    icon_names={'instagram','facebook','youtube','whatsapp','tiktok','linkedin'}
    if any(t in label for t in ['logo','icone']) or any(norm(Path(t).stem) in icon_names for t in rec['rotulos']): return "marcas-icones-e-identidade"
    if any(t in norm(stems) for t in ["parceiros"]): return "parceiros"
    if "noticias-e-midias" in topics: return "galerias-noticias-e-eventos"
    if "servicos-e-projetos" in topics: return "servicos-e-projetos"
    if "doacoes-e-participacao" in topics: return "doacoes-e-campanhas"
    if any(t in norm(stems) for t in ["nossaequipe", "instala"]): return "instalacoes-e-equipe"
    if rec.get("paginas_conteudo"): return "institucional"
    return "sem-contexto-especifico"


def doc_group(rec):
    label = norm(" ".join(rec["rotulos"]) + " " + unquote(rec["_path"].name))
    if any(k in label for k in ["estatuto", "assembleia"]): return "governanca"
    if "viagem" in label: return "campanhas"
    if any(k in label for k in ["portfolio", "portifolio"]): return "portfolios"
    if "relat" in label or "rlat" in label: return "relatorios-de-atividades"
    return "prestacao-de-contas"


def organize(records, pages):
    page_map = {p["id"]: p for p in pages}
    unique = {}
    copied = 0
    format_ext = {"JPEG": ".jpg", "PNG": ".png", "GIF": ".gif", "AVIF": ".avif", "WEBP": ".webp", "SVG": ".svg"}
    for rec in records:
        rec["duplicado_de"] = unique.get(rec["sha256"], {}).get("id", "")
        if rec["duplicado_de"]:
            rec["organizado"] = unique[rec["sha256"]]["organizado"]
            continue
        ext = rec["extensao_original"]
        base = rec["rotulos"][0] if rec["rotulos"] else unquote(rec["_path"].stem)
        if rec["tipo"] == "imagem":
            group = image_group(rec, page_map); rec["grupo"] = group
            ext = format_ext.get(rec.get("formato_real"), ext)
            folder = "03_imagens/" + group
        elif rec["tipo"] == "documento":
            group = doc_group(rec); rec["grupo"] = group; folder = "05_documentos/" + group
        elif rec["tipo"] == "video": folder = "04_videos/locais"; base = rec["titulo"]
        else:
            kind = "html-fontes" if rec["tipo"] in {"pagina", "html-tecnico", "html-erro", "html"} else rec["tipo"]
            folder = "07_tecnico/" + kind
            if rec["tipo"] == "pagina": base = rec["titulo"]
        name = f"{rec.get('asset_id', rec['id'])}--{slug(base, 85)}{ext}"
        target = DEST / folder / name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(rec["_path"], target)
        rec["organizado"] = target.relative_to(DEST).as_posix()
        unique[rec["sha256"]] = rec
        copied += rec["bytes"]
    # Duplicatas continuam com seus próprios metadados, referenciando uma cópia idêntica.
    for rec in records:
        if rec["duplicado_de"]:
            master = unique[rec["sha256"]]
            rec["grupo"] = master.get("grupo", "")
    return unique, copied


def image_previews(records):
    images = [r for r in records if r["tipo"] == "imagem" and not r["duplicado_de"]]
    families = defaultdict(list)
    for rec in images: families[rec["familia"]].append(rec)
    best = set()
    for family in families.values():
        best.add(max(family, key=lambda r: (r.get("largura", 0) * r.get("altura", 0), r["bytes"]))["id"])
    for rec in images:
        rec["melhor_da_familia"] = rec["id"] in best
        if rec.get("status") != "lido" or rec.get("formato_real") == "SVG": continue
        thumb = DEST / "09_previsualizacoes/imagens" / (rec["asset_id"] + ".jpg")
        thumb.parent.mkdir(parents=True, exist_ok=True)
        try:
            with Image.open(rec["_path"]) as original:
                original.seek(0)
                im = ImageOps.exif_transpose(original).convert("RGBA")
                im.thumbnail((420, 280), Image.Resampling.LANCZOS)
                bg = Image.new("RGB", im.size, "#f4f0ec"); bg.paste(im, mask=im.getchannel("A"))
                bg.save(thumb, quality=84)
            rec["miniatura"] = thumb.relative_to(DEST).as_posix()
        except Exception as exc:
            rec["erro_miniatura"] = str(exc)
    representatives = sorted([r for r in images if r["id"] in best and r.get("miniatura")], key=lambda r: (r.get("grupo", ""), r["asset_id"]))
    font = ImageFont.truetype("C:/Windows/Fonts/arial.ttf", 16)
    small = ImageFont.truetype("C:/Windows/Fonts/arial.ttf", 12)
    for n, start in enumerate(range(0, len(representatives), 60), 1):
        sheet = Image.new("RGB", (1500, 1680), "white"); draw = ImageDraw.Draw(sheet)
        draw.text((20, 12), f"AACI | Imagens representativas | Folha {n} | IDs consultáveis no catálogo", font=font, fill="#4b1025")
        for k, rec in enumerate(representatives[start:start+60]):
            x, y = (k % 6) * 250, 45 + (k // 6) * 162
            with Image.open(DEST / rec["miniatura"]) as im:
                im.thumbnail((234, 118)); sheet.paste(im, (x + (250-im.width)//2, y))
            draw.text((x+9, y+120), f"{rec['asset_id']} | {rec.get('largura',0)}x{rec.get('altura',0)}", font=small, fill="#222222")
            label = (rec["rotulos"][0] if rec["rotulos"] else rec.get("grupo", ""))[:32]
            draw.text((x+9, y+137), label, font=small, fill="#66575c")
        out = DEST / "09_previsualizacoes/folhas-de-contato" / f"imagens-{n:02}.jpg"
        out.parent.mkdir(parents=True, exist_ok=True); sheet.save(out, quality=90)
    return representatives


def analyze_pdfs(records):
    queue = []
    for rec in [r for r in records if r["tipo"] == "documento"]:
        doc = fitz.open(rec["_path"])
        rec["numero_paginas"] = len(doc)
        rec["titulo"] = next((t for t in rec["rotulos"] if t), unquote(rec["_path"].stem))
        text_pages = []
        no_text_pages = []
        for i, page in enumerate(doc):
            text = page.get_text(sort=True)
            text_pages.append({"pagina": i+1, "texto": text, "metodo": "texto_pdf"})
            useful = re.sub(r"Digitalizado com CamScanner|CamScanner|Scanned with|\W", "", text, flags=re.I)
            if len(useful) < 55:
                no_text_pages.append(i+1)
                img_path = TMP / "ocr-input" / f"{rec['asset_id']}--p{i+1:03}.png"
                img_path.parent.mkdir(parents=True, exist_ok=True)
                scale = min(2.0, 2400 / max(page.rect.width, page.rect.height))
                page.get_pixmap(matrix=fitz.Matrix(scale, scale), alpha=False).save(img_path)
                queue.append({"documento": rec["asset_id"], "pagina": i+1, "imagem": str(img_path),
                              "saida": str(TMP / "ocr-output" / f"{rec['asset_id']}--p{i+1:03}.json")})
        rec["paginas_sem_texto_selecionavel"] = no_text_pages
        rec["caracteres_texto_nativo"] = sum(len(p["texto"]) for p in text_pages)
        rec["texto_paginas"] = text_pages
        preview = DEST / "09_previsualizacoes/pdfs" / f"{rec['asset_id']}.jpg"
        preview.parent.mkdir(parents=True, exist_ok=True)
        pix = doc[0].get_pixmap(matrix=fitz.Matrix(500/doc[0].rect.width, 500/doc[0].rect.width), alpha=False)
        pix.save(preview)
        rec["miniatura"] = preview.relative_to(DEST).as_posix()
        (DEST / "02_textos/documentos").mkdir(parents=True, exist_ok=True)
        out = DEST / "02_textos/documentos" / (rec["asset_id"] + "--" + slug(rec["titulo"], 65) + ".txt")
        rec["texto_arquivo"] = out.relative_to(DEST).as_posix()
        write_doc_text(rec)
        doc.close()
    (TMP / "ocr-output").mkdir(parents=True, exist_ok=True)
    dump(TMP / "ocr-fila.json", queue)
    return queue


def write_doc_text(rec):
    header = f"{rec['asset_id']} | {rec['titulo']}\nOrigem: {rec['origem']}\nURL: {rec['urls'][0] if rec['urls'] else ''}\n"
    content = "\n\n".join(f"--- PÁGINA {p['pagina']} | {p['metodo']} ---\n{p['texto']}" for p in rec["texto_paginas"])
    (DEST / rec["texto_arquivo"]).write_text(header + "\n" + content, encoding="utf-8")


def analyze_videos(records):
    import imageio_ffmpeg
    executable = imageio_ffmpeg.get_ffmpeg_exe()
    for rec in [r for r in records if r["tipo"] == "video"]:
        result = subprocess.run([executable, "-hide_banner", "-i", str(rec["_path"])], capture_output=True, text=True, encoding="utf-8", errors="replace")
        output = result.stderr
        duration = re.search(r"Duration:\s*(\d+):(\d+):(\d+(?:\.\d+)?)", output)
        seconds = sum(float(v)*factor for v, factor in zip(duration.groups(), [3600,60,1])) if duration else 0
        res = re.search(r"Video:.*?\b(\d{2,5})x(\d{2,5})\b", output)
        rec["duracao_segundos"] = round(seconds, 2)
        rec["duracao"] = f"{int(seconds)//60:02}:{int(seconds)%60:02}"
        if res: rec["largura"], rec["altura"] = map(int, res.groups())
        rec["tem_audio"] = "Audio:" in output
        rec["analise_audio"] = "áudio preservado; sem transcrição automática"
        # A decodificação integral detecta arquivos interrompidos/corrompidos.
        checked = subprocess.run([executable, "-v", "error", "-i", str(rec["_path"]), "-f", "null", "-"], capture_output=True, text=True, encoding="utf-8", errors="replace")
        rec["validacao_video"] = "decodificacao_integral_ok" if checked.returncode == 0 and not checked.stderr.strip() else "avisos_de_decodificacao"
        rec["avisos_video"] = checked.stderr[:2000]
        frames = []
        for i, fraction in enumerate([.08, .35, .65, .90], 1):
            frame = DEST / "09_previsualizacoes/videos" / f"{rec['asset_id']}--quadro-{i}.jpg"
            frame.parent.mkdir(parents=True, exist_ok=True)
            subprocess.run([executable, "-v", "error", "-y", "-ss", str(seconds*fraction), "-i", str(rec["_path"]), "-frames:v", "1", "-vf", "scale=600:-1", str(frame)], capture_output=True)
            if frame.exists(): frames.append(frame.relative_to(DEST).as_posix())
        rec["quadros"] = frames
        rec["miniatura"] = frames[0] if frames else ""


def cache_inventory():
    entries = []
    with zipfile.ZipFile(SOURCE / "hts-cache/new.zip") as archive:
        for info in archive.infolist():
            data = archive.read(info)
            entries.append({"url_entrada": info.filename, "bytes": info.file_size, "crc32": f"{info.CRC:08x}",
                            "sha256": hashlib.sha256(data).hexdigest(), "estado": "lido_e_crc_verificado"})
    return entries


def export_outputs(records, pages, links, external_videos, transfers, cache, representatives, copied_bytes):
    clean_records = [{k: v for k, v in r.items() if not k.startswith("_")} for r in records]
    stats = {"data_analise": NOW, "origem": str(SOURCE), "destino": str(DEST), "arquivos_origem": len(records),
        "bytes_origem": sum(r["bytes"] for r in records), "arquivos_unicos": len({r['sha256'] for r in records}),
        "copias_organizadas_bytes": copied_bytes, "duplicados_exatos": sum(bool(r["duplicado_de"]) for r in records),
        "tipos": dict(Counter(r["tipo"] for r in records)), "extensoes": dict(Counter(r["extensao_original"] for r in records)),
        "paginas_publicas": len(pages), "imagens_representativas": len(representatives),
        "familias_de_imagem": len({r["familia"] for r in records if r["tipo"] == "imagem"}),
        "paginas_pdf": sum(r.get("numero_paginas", 0) for r in records),
        "videos_externos_catalogados": len(external_videos), "entradas_cache_lidas": len(cache),
        "transferencias_http": len(transfers), "status_http": dict(Counter(t["status_http"] for t in transfers))}
    dataset = {"estatisticas": stats, "arquivos": clean_records, "paginas": pages, "links": links,
               "videos_externos": external_videos, "transferencias": transfers, "cache": cache}
    dump(DEST / "08_catalogos/acervo.json", dataset)
    fields = ["id", "asset_id", "tipo", "grupo", "origem", "organizado", "bytes", "sha256", "duplicado_de", "extensao_original", "formato_real", "largura", "altura", "numero_paginas", "duracao", "titulo", "rotulos", "paginas", "urls", "status", "status_http"]
    write_csv(DEST / "08_catalogos/inventario-completo.csv", clean_records, fields)
    write_csv(DEST / "08_catalogos/duplicados-exatos.csv", [r for r in clean_records if r["duplicado_de"]], ["id", "origem", "sha256", "duplicado_de", "organizado"])
    write_csv(DEST / "08_catalogos/paginas.csv", pages, ["id", "titulo", "url", "origem", "tema", "status_conteudo", "caracteres_texto", "imagens", "documentos", "videos_locais"])
    write_csv(DEST / "08_catalogos/imagens.csv", [r for r in clean_records if r["tipo"] == "imagem"], fields + ["familia", "melhor_da_familia", "miniatura"])
    write_csv(DEST / "08_catalogos/documentos.csv", [r for r in clean_records if r["tipo"] == "documento"], fields + ["caracteres_texto_nativo", "paginas_sem_texto_selecionavel", "texto_arquivo"])
    write_csv(DEST / "08_catalogos/videos-locais.csv", [r for r in clean_records if r["tipo"] == "video"], fields + ["duracao_segundos", "tem_audio", "validacao_video", "analise_audio"])
    write_csv(DEST / "04_videos/videos-externos.csv", external_videos, ["titulo", "url", "duracao_declarada", "data_publicacao", "descricao", "paginas"])
    write_csv(DEST / "06_links_e_informacoes/links-publicos.csv", links, ["pagina", "rotulo", "url", "presente_localmente", "arquivo_local_id", "href_capturado"])
    write_csv(DEST / "08_catalogos/transferencias-httrack.csv", transfers, ["url", "status_http", "mime", "caminho_cache", "pagina_referente", "tamanho"])
    write_csv(DEST / "08_catalogos/entradas-cache.csv", cache, ["url_entrada", "bytes", "crc32", "sha256", "estado"])
    for page in pages:
        p = DEST / "02_textos/paginas" / f"{page['id']}--{slug(page['titulo'], 70)}.txt"
        p.parent.mkdir(parents=True, exist_ok=True)
        page["texto_arquivo"] = p.relative_to(DEST).as_posix()
        p.write_text(f"{page['id']} | {page['titulo']}\nURL: {page['url']}\nOrigem: {page['origem']}\nEstado: {page['status_conteudo']}\n\n{page['texto']}\n", encoding="utf-8")
    dump(DEST / "08_catalogos/acervo.json", dataset)
    return dataset


def main():
    if not SOURCE.is_dir(): raise SystemExit(f"Origem não encontrada: {SOURCE}")
    if (DEST/'08_catalogos/acervo.json').exists():
        raise SystemExit('Já existe uma coleção organizada. Preserve-a ou use outro destino antes de executar uma extração completa novamente.')
    DEST.mkdir(parents=True, exist_ok=True); TMP.mkdir(parents=True, exist_ok=True)
    print("Lendo todos os arquivos e calculando SHA-256...", flush=True)
    records = classify(load_capture())
    transfers = parse_httrack(records)
    print("Analisando páginas, textos, links e dados estruturados Wix...", flush=True)
    pages, links, external_videos, _ = analyze_pages(records)
    print(f"Páginas: {len(pages)}. Organizando cópias únicas...", flush=True)
    unique, copied = organize(records, pages)
    print("Gerando miniaturas e folhas de contato...", flush=True)
    representatives = image_previews(records)
    print("Lendo todas as páginas dos PDFs...", flush=True)
    queue = analyze_pdfs(records)
    print(f"Fila OCR: {len(queue)} páginas. Validando e identificando vídeos...", flush=True)
    analyze_videos(records)
    print("Lendo e verificando CRC das entradas do cache ZIP...", flush=True)
    cache = cache_inventory()
    dataset = export_outputs(records, pages, links, external_videos, transfers, cache, representatives, copied)
    print(json.dumps(dataset["estatisticas"], ensure_ascii=False, indent=2))
    print("Arquivos OCR em", TMP / "ocr-fila.json", flush=True)


if __name__ == "__main__": main()
