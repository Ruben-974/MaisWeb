"""Complementa OCR, nomes, índices e páginas de consulta do acervo local."""
from __future__ import annotations
import argparse
import csv
import hashlib
import html
import json
import os
import re
from collections import Counter, defaultdict
from pathlib import Path
from urllib.parse import quote, unquote, urlsplit
from PIL import Image, ImageDraw, ImageFont, ImageOps
import mapear_acervo_aaci as base

DEST, SOURCE, TMP = base.DEST, base.SOURCE, base.TMP
DATA = DEST / "08_catalogos/acervo.json"

# Rótulos editoriais atribuídos após inspeção visual das folhas de contato.
REVIEWED = {
    "IMG-0054": ("StarToys", "parceiros"), "IMG-0084": ("Mesa Brasil SESC", "parceiros"),
    "IMG-0089": ("Universidade Federal de Juiz de Fora", "parceiros"), "IMG-0099": ("Havan", "parceiros"),
    "IMG-0109": ("Instituto Embelleze", "parceiros"), "IMG-0112": ("Coca-Cola FEMSA", "parceiros"),
    "IMG-0117": ("Ri Happy", "parceiros"), "IMG-0126": ("Fiat Delta", "parceiros"),
    "IMG-0150": ("Gente em Primeiro Lugar", "parceiros"), "IMG-0168": ("Moinho Zona Norte", "parceiros"),
    "IMG-0173": ("Pais e Filhos", "parceiros"), "IMG-0203": ("Stop Hunger", "parceiros"),
    "IMG-0228": ("Criança Esperança", "parceiros"), "IMG-0256": ("Engenheiros Sem Fronteiras - Núcleo Juiz de Fora", "parceiros"),
    "IMG-0263": ("Thomson Reuters", "parceiros"), "IMG-0268": ("Bom Brasileiro", "parceiros"),
    "IMG-0292": ("Pátria Voluntária", "parceiros"), "IMG-0298": ("Associação Esportiva e Recreativa Becton Dickinson", "parceiros"),
    "IMG-0300": ("Da Festa", "parceiros"), "IMG-0324": ("Plenarius Escola de Profissões", "parceiros"),
    "IMG-0336": ("MRS Logística", "parceiros"), "IMG-0341": ("Grupo Bahamas", "parceiros"),
    "IMG-0353": ("Logo AACI com personagens", "marcas-icones-e-identidade"),
    "IMG-0445": ("Personagens do logo AACI", "marcas-icones-e-identidade"),
    "IMG-0513": ("Logo Vinho AACI", "marcas-icones-e-identidade"),
    "IMG-0518": ("Logo AACI em fundo claro", "marcas-icones-e-identidade"),
    "IMG-0486": ("Banner institucional - crianças abraçadas", "institucional"),
    "IMG-0457": ("Banner institucional - criança sorrindo", "institucional"),
    "IMG-0371": ("QR code Pix publicado na página Como Ajudar", "doacoes-e-campanhas"),
    "IMG-0468": ("QR code publicado no site - finalidade a confirmar", "doacoes-e-campanhas"),
    "IMG-0392": ("Contatos gráficos do Apadrinhamento Afetivo", "servicos-e-projetos"),
    "IMG-0538": ("Contatos gráficos do Serviço de Convivência", "servicos-e-projetos"),
    "IMG-0476": ("Organograma da AACI", "instalacoes-e-equipe"),
    "IMG-0407": ("Etapas do telemarketing filantrópico", "doacoes-e-campanhas"),
    "IMG-0487": ("AACI e os ODS 8 16 e 17", "institucional"),
    "IMG-0502": ("AACI e os ODS 1 2 e 3", "institucional"),
    "IMG-0505": ("AACI e os ODS 4 5 e 10", "institucional"),
    "IMG-0510": ("ODS 5 - Igualdade de gênero", "institucional"),
}


def read_data(): return json.loads(DATA.read_text(encoding="utf-8"))


def prepare_ocr():
    data = read_data()
    queue = json.loads((TMP / "ocr-fila.json").read_text(encoding="utf-8"))
    image_count = 0
    for rec in data["arquivos"]:
        if rec["tipo"] != "imagem" or not rec.get("melhor_da_familia") or max(rec.get("largura", 0), rec.get("altura", 0)) < 180:
            continue
        source = SOURCE / rec["origem"]
        try:
            with Image.open(source) as original:
                im = ImageOps.exif_transpose(original).convert("RGBA")
                im.thumbnail((2400, 2400), Image.Resampling.LANCZOS)
                bg = Image.new("RGB", im.size, "white"); bg.paste(im, mask=im.getchannel("A"))
                target = TMP / "ocr-input" / f"{rec['asset_id']}.png"; bg.save(target)
            queue.append({"documento": rec["asset_id"], "pagina": 1, "imagem": str(target),
                          "saida": str(TMP / "ocr-output" / f"{rec['asset_id']}.json")})
            image_count += 1
        except Exception as exc: print("OCR imagem indisponível", rec.get("asset_id"), exc)
    base.dump(TMP / "ocr-fila-completa.json", queue)
    print(f"Fila OCR: {len(queue)} itens; {image_count} imagens representativas e {len(queue)-image_count} páginas PDF.")


def curate(data):
    family_labels = {}
    page_map={p['id']:p for p in data['paginas']}
    for rec in data["arquivos"]:
        if rec.get("asset_id") in REVIEWED: family_labels[rec["familia"]] = REVIEWED[rec["asset_id"]]
    for rec in data["arquivos"]:
        if rec["tipo"] != "imagem": continue
        rec['grupo']=base.image_group(rec,page_map)
        if rec.get("familia") in family_labels:
            label, group = family_labels[rec["familia"]]
            rec["rotulo_editorial"] = label; rec["grupo"] = group
        rec["baixa_resolucao"] = max(rec.get("largura", 0), rec.get("altura", 0)) < 180
        if rec.get("duplicado_de"): continue
        label = rec.get("rotulo_editorial") or next((x for x in rec["rotulos"] if x and not re.fullmatch(r"[\d .]+", Path(x).stem)), "")
        if not label or re.fullmatch(r"(?:c696b8_)?[a-f0-9_~.]+(?:png|jpg)?", label):
            label = rec.get("grupo", "imagem")
        old = DEST / rec["organizado"]
        target = DEST / "03_imagens" / rec["grupo"] / f"{rec['asset_id']}--{base.slug(label,75)}{old.suffix}"
        if not target.resolve().is_relative_to(DEST.resolve()): raise ValueError("Destino fora da coleção")
        if target != old:
            target.parent.mkdir(parents=True, exist_ok=True)
            old.rename(target)
            rec["organizado"] = target.relative_to(DEST).as_posix()
    by_id = {r["id"]: r for r in data["arquivos"]}
    for rec in data["arquivos"]:
        if rec.get("duplicado_de"): rec["organizado"] = by_id[rec["duplicado_de"]]["organizado"]


def merge_ocr(data):
    successes = errors = 0
    for rec in data["arquivos"]:
        if rec["tipo"] == "documento":
            native_doc=base.fitz.open(SOURCE/rec['origem'])
            for page in rec["texto_paginas"]:
                path = TMP / "ocr-output" / f"{rec['asset_id']}--p{page['pagina']:03}.json"
                if path.exists():
                    result = json.loads(path.read_text(encoding="utf-8-sig"))
                    page["texto_nativo"] = native_doc[page['pagina']-1].get_text(sort=True)
                    page["texto"] = result.get("texto", "") or page["texto"]
                    page["metodo"] = result["metodo"]
                    page["estado_ocr"] = result["estado"]
                    if result["estado"] == "ok": successes += 1
                    else: errors += 1
            native_doc.close()
            rec["caracteres_texto_total"] = sum(len(p["texto"]) for p in rec["texto_paginas"])
            rec["paginas_ocr"] = sum(p["metodo"].startswith("OCR") for p in rec["texto_paginas"])
            base.write_doc_text(rec)
        if rec["tipo"] == "imagem" and rec.get("melhor_da_familia"):
            path = TMP / "ocr-output" / f"{rec['asset_id']}.json"
            if path.exists():
                result = json.loads(path.read_text(encoding="utf-8-sig"))
                rec["texto_ocr"] = result.get("texto", "")
                rec["estado_ocr"] = result["estado"]
                rec["texto_arquivo"] = f"02_textos/imagens/{rec['asset_id']}.txt"
                out = DEST / rec["texto_arquivo"]; out.parent.mkdir(parents=True, exist_ok=True)
                out.write_text(f"{rec['asset_id']} | OCR Windows pt-BR, sujeito a erros\nOrigem: {rec['origem']}\n\n{rec['texto_ocr']}\n", encoding="utf-8")
                if result["estado"] == "ok": successes += 1
                else: errors += 1
    data["estatisticas"].update({"itens_ocr_ok": successes, "itens_ocr_erro": errors,
        "paginas_pdf_ocr": sum(r.get("paginas_ocr",0) for r in data["arquivos"]),
        "imagens_com_ocr": sum("texto_ocr" in r for r in data["arquivos"]),
        "familias_apenas_baixa_resolucao": sum(r.get("melhor_da_familia",False) and r.get("baixa_resolucao",False) for r in data["arquivos"])})


def information(data):
    contacts = defaultdict(lambda: {"paginas": [], "fontes": []})
    for page in data["paginas"]:
        for typ, regex in [("email", r"[\w.+-]+@[\w.-]+\.[a-zA-Z]{2,}"),
                           ("telefone", r"\(?32\)?[ .-]*9?\d{4}[ .-]?\d{4}"),
                           ("cnpj", r"\b\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2}\b")]:
            for value in set(re.findall(regex, page["texto"])):
                item = contacts[(typ, value)]
                item["paginas"].append(page["id"]); item["fontes"].append(page["url"])
    rows = [{"tipo": typ, "valor": value, "paginas": sorted(set(meta["paginas"])), "fontes": sorted(set(meta["fontes"]))} for (typ,value),meta in contacts.items()]
    by_asset={a.get('asset_id'):a for a in data['arquivos']}
    for typ,value,aid in [('email','apadrinhamento@aaci.org.br','IMG-0392'),('telefone','(32) 3211-5475','IMG-0392'),('telefone','(32) 98889-0665','IMG-0392'),('endereco','Rua General Almerindo da Silva Gomes, 133, Nova Era, Juiz de Fora','IMG-0392'),('endereco','Rua General Almerindo da Silva Gomes, 162, Nova Era, Juiz de Fora','IMG-0538')]:
        asset=by_asset[aid]
        rows.append({'tipo':typ,'valor':value,'paginas':asset.get('paginas_conteudo',[]),'fontes':asset['urls'],'imagens':[aid],'metodo':'leitura visual da imagem'})
    rows.extend([{'tipo':'endereco','valor':'Rua Doutor Dias da Cruz, 487, Nova Era, Juiz de Fora - MG','paginas':['PAG-017'],'fontes':['https://www.aaci.org.br/'],'metodo':'texto HTML'}, {'tipo':'endereco','valor':'Rua Guimarães Júnior, 90, Nova Era, Juiz de Fora - MG','paginas':['PAG-009','PAG-010','PAG-034'],'fontes':['https://www.aaci.org.br/contato'],'metodo':'texto HTML'}])
    base.write_csv(DEST / "06_links_e_informacoes/contatos-extraidos.csv", rows, ["tipo", "valor", "paginas", "imagens", "fontes", "metodo"])
    forms = [{"pagina": p["id"], "titulo": p["titulo"], **form} for p in data["paginas"] for form in p["formularios"]]
    base.write_csv(DEST / "06_links_e_informacoes/formularios.csv", forms, ["pagina", "titulo", "campos", "acao", "estado"])
    data["contatos_extraidos"] = rows
    data["formularios"] = forms
    missing = [l for l in data["links"] if not l["presente_localmente"] and not l["url"].startswith(("mailto:", "tel:"))]
    base.write_csv(DEST / "06_links_e_informacoes/referencias-sem-arquivo-local.csv", missing, ["pagina", "rotulo", "url", "href_capturado"])
    data["estatisticas"]["formularios_capturados"] = len(forms)
    data["estatisticas"]["paginas_conteudo_escasso"] = sum(p["status_conteudo"] != "texto_recuperado" for p in data["paginas"])


def e(value): return html.escape(str(value), quote=True)


STYLE = """
:root{--ink:#28232a;--wine:#64152e;--muted:#6b646a;--line:#e6dde0;--cream:#fbf7f4}*{box-sizing:border-box}body{font:16px/1.6 Arial,sans-serif;color:var(--ink);background:var(--cream);margin:0}a{color:var(--wine);text-underline-offset:3px}header{background:#fff;border-bottom:1px solid var(--line);padding:36px max(24px,calc((100vw - 1240px)/2)) 26px}header p{max-width:850px;color:var(--muted)}h1{font:700 clamp(30px,4vw,48px)/1.15 Georgia,serif;margin:8px 0 16px}h2{font:700 28px/1.25 Georgia,serif}h3{font-size:17px;line-height:1.4;margin:9px 0}main{max-width:1288px;padding:24px;margin:auto}.eyebrow{font-size:12px;text-transform:uppercase;letter-spacing:1px;font-weight:bold;color:var(--wine)}nav,.actions,.filters{display:flex;gap:10px;flex-wrap:wrap}nav a,.button{display:inline-block;padding:9px 15px;text-decoration:none;border:1px solid var(--line);background:white;border-radius:8px;font-weight:bold;font-size:14px}nav a:hover,.button:hover{border-color:var(--wine)}.stats{display:grid;grid-template-columns:repeat(auto-fit,minmax(125px,1fr));gap:12px;margin:24px 0}.stat{border:1px solid var(--line);border-radius:12px;background:#fff;padding:18px}.stat strong{display:block;color:var(--wine);font-size:26px}.stat span{font-size:13px;color:var(--muted)}.notice{border-left:4px solid var(--wine);padding:16px 20px;background:#fff;border-radius:0 8px 8px 0}.toolbar{background:#fff;padding:18px;border:1px solid var(--line);border-radius:12px;margin:24px 0;position:relative}.filters{align-items:center}label{font-size:14px;font-weight:bold}input[type=search],select{font:inherit;padding:10px 12px;border:1px solid #b9afb3;border-radius:6px;background:#fff;min-width:180px}input[type=search]{flex:1}input[type=checkbox]{width:18px;height:18px;vertical-align:middle}.cards{display:grid;grid-template-columns:repeat(auto-fill,minmax(235px,1fr));gap:18px}.card{background:#fff;border:1px solid var(--line);border-radius:12px;overflow:hidden;min-width:0}.card img{width:100%;height:180px;object-fit:contain;background:#f1edeb;display:block}.card-body{padding:17px}.card p{font-size:14px;color:var(--muted);margin:8px 0}.tag{display:inline-block;font-size:11px;background:#f3e7eb;color:var(--wine);padding:3px 7px;border-radius:5px;margin-right:5px}.tag.low{background:#fff2cf;color:#705000}.meta{font-size:12px;overflow-wrap:anywhere}.section{margin:36px 0}table{border-collapse:collapse;background:white;width:100%;font-size:14px}th,td{padding:12px;text-align:left;vertical-align:top;border-bottom:1px solid var(--line)}th{background:#f1e7ea}td{overflow-wrap:anywhere}pre{white-space:pre-wrap;overflow-wrap:anywhere;background:white;padding:24px;border:1px solid var(--line);border-radius:12px;font:15px/1.75 Arial,sans-serif}.scroll-table{overflow-x:auto}.small{font-size:13px;color:var(--muted)}footer{padding:30px 24px;text-align:center;color:var(--muted);font-size:13px}video{width:100%;max-height:420px;background:#111}details{background:#fff;padding:14px 18px;border:1px solid var(--line);border-radius:8px;margin:12px 0}summary{cursor:pointer;font-weight:bold}:focus-visible{outline:3px solid #ba781e;outline-offset:3px}[hidden]{display:none!important}@media(max-width:600px){header{padding:26px 20px}main{padding:20px}.cards{grid-template-columns:1fr}input[type=search],select{width:100%}.card img{height:220px}.stats{grid-template-columns:repeat(2,1fr)}}
"""


def shell(title, content, prefix=""):
    return f'<!doctype html><html lang="pt-BR"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{e(title)} | Acervo AACI</title><link rel="stylesheet" href="{prefix}catalogo.css"></head><body>{content}<footer>Inventário local da captura HTTrack de 13/11/2026. Originais preservados em AACI.</footer></body></html>'


def render_catalog(data):
    assets = data["arquivos"]; pages = data["paginas"]; stat = data["estatisticas"]
    asset_map = {a["id"]:a for a in assets}
    page_map = {p["id"]:p for p in pages}
    (DEST/"catalogo.css").write_text(STYLE,encoding="utf-8")
    for page in pages:
        page["consulta_html"] = f"01_paginas/{page['id']}--{base.slug(page['titulo'],65)}.html"
    navigation = '<nav><a href="index.html">Visão geral</a><a href="imagens.html">Imagens</a><a href="documentos.html">Documentos</a><a href="videos.html">Vídeos</a><a href="paginas.html">Páginas e textos</a><a href="Relatorio-do-acervo-AACI.pdf">Relatório PDF</a></nav>'
    def header(title, text): return f'<header><div class="eyebrow">AACI · acervo organizado · 13/11/2026</div><h1>{e(title)}</h1><p>{text}</p>{navigation}</header>'
    cards=[]
    for value,label in [(stat['arquivos_origem'],'arquivos inventariados'),(len(pages),'páginas capturadas'),(stat['tipos']['imagem'],'arquivos de imagem'),(stat['tipos']['documento'],'documentos PDF'),(stat['tipos']['video'],'vídeos locais'),(stat['videos_externos_catalogados'],'vídeos referenciados')]:
        cards.append(f'<div class="stat"><strong>{value}</strong><span>{label}</span></div>')
    topics=Counter(p['tema'] for p in pages)
    overview=header('Tudo o que foi extraído, em um só lugar.','Páginas, imagens, vídeos, documentos e informações públicas da cópia local do site da AACI. Use os catálogos para encontrar os arquivos sem navegar pelos nomes técnicos do HTTrack.')
    overview+='<main><div class="stats">'+''.join(cards)+'</div><div class="notice"><strong>A coleção mantém o que foi efetivamente capturado.</strong> Há referências externas, miniaturas em baixa resolução e páginas de erro. Vídeos do YouTube e formulários dependem dos serviços originais; seus links e estruturas foram catalogados.</div>'
    overview+='<section class="section"><h2>Explore o conteúdo</h2><div class="cards">'
    for file,title,text in [('imagens.html','Banco de imagens',f'{stat["familias_de_imagem"]} famílias de mídia, com miniaturas, dimensões, contexto e variantes.'),('documentos.html','Documentos e relatórios',f'26 PDFs, somando {stat["paginas_pdf"]} páginas, com extração de texto e OCR identificado.'),('videos.html','Vídeos locais e referências','Reprodução dos 4 MP4 locais, quadros de prévia e 12 títulos externos.'),('paginas.html','Conteúdo por página','Textos limpos, links e mídias associados a cada uma das 45 páginas.')]:
        overview+=f'<article class="card"><div class="card-body"><h3><a href="{file}">{title}</a></h3><p>{e(text)}</p></div></article>'
    overview+='</div></section><section class="section"><h2>Inventários completos</h2><div class="actions">'
    for file,label in [('08_catalogos/inventario-completo.csv','Todos os 949 arquivos (CSV)'),('08_catalogos/acervo.json','Dados completos (JSON)'),('08_catalogos/duplicados-exatos.csv','Duplicatas e correspondências'),('06_links_e_informacoes/contatos-extraidos.csv','Contatos extraídos'),('06_links_e_informacoes/referencias-sem-arquivo-local.csv','Referências sem arquivo local'),('00_LEIA-ME.md','Como usar a coleção')]:
        overview+=f'<a class="button" href="{e(file)}">{e(label)}</a>'
    overview+='</div></section><section class="section"><h2>Conteúdo por tema</h2><ul>'+''.join(f'<li>{e(k)}: {v} páginas</li>' for k,v in sorted(topics.items()))+'</ul></section><section class="section"><h2>Pontos que precisam de contexto</h2><ul><li>Os endereços e telefones variam entre páginas e imagens. O acervo conserva as versões encontradas.</li><li>Textos obtidos por OCR são aproximações pesquisáveis; confira o PDF ou a imagem original.</li><li>Arquivos de infraestrutura, fontes e logs estão em <code>07_tecnico</code>, separados do material público.</li><li>As páginas em <code>01_paginas</code> são fichas de consulta. O site espelhado original continua em <code>../AACI</code>.</li></ul></section></main>'
    (DEST/'index.html').write_text(shell('Visão geral',overview),encoding='utf-8')
    search_script='''<script>const search=document.querySelector('[data-search]'),group=document.querySelector('[data-group]'),variants=document.querySelector('[data-variants]'),cards=[...document.querySelectorAll('[data-card]')],count=document.querySelector('[data-count]');function update(){const q=search.value.normalize('NFD').replace(/[\\u0300-\\u036f]/g,'').toLowerCase();let n=0;for(const c of cards){const ok=c.dataset.search.includes(q)&&(!group||!group.value||c.dataset.group===group.value)&&(!variants||variants.checked||c.dataset.best==='true');c.hidden=!ok;if(ok)n++}count.textContent=n+' itens exibidos'}search.addEventListener('input',update);group?.addEventListener('change',update);variants?.addEventListener('change',update);update();</script>'''
    def toolbar(groups,variants=False):
        return '<div class="toolbar"><div class="filters"><label for="search">Pesquisar</label><input id="search" type="search" data-search placeholder="Nome, ID, tema ou texto…"><label for="group">Grupo</label><select id="group" data-group><option value="">Todos os grupos</option>'+''.join(f'<option value="{e(g)}">{e(g)}</option>' for g in sorted(set(groups)))+'</select>'+('<label><input type="checkbox" data-variants> Mostrar todas as variantes</label>' if variants else '')+'</div><p class="small" data-count aria-live="polite"></p></div>'
    images=[a for a in assets if a['tipo']=='imagem' and not a['duplicado_de']]
    content=header('Imagens','Uma visualização por família aparece inicialmente. Ative as variantes para ver todos os arquivos únicos. Os rótulos vêm do site, da página de origem ou da inspeção visual registrada.')+'<main>'+toolbar([a.get('grupo','') for a in images],True)+'<div class="cards">'
    for a in images:
        label=a.get('rotulo_editorial') or (a['rotulos'][0] if a['rotulos'] else a['asset_id'])
        context=', '.join(page_map[p]['titulo'] for p in a.get('paginas_conteudo',[])[:4] if p in page_map)
        query=base.norm(' '.join([a['asset_id'],label,context,a.get('grupo',''),a.get('texto_ocr','')]))
        image=a.get('miniatura') or a['organizado']
        content+=f'<article class="card" data-card data-group="{e(a.get("grupo",""))}" data-best="{str(a.get("melhor_da_familia",False)).lower()}" data-search="{e(query)}"><a href="{e(a["organizado"])}"><img loading="lazy" src="{e(image)}" alt="{e(label)}"></a><div class="card-body"><span class="tag">{a["asset_id"]}</span>'+('<span class="tag low">Baixa resolução</span>' if a.get('baixa_resolucao') else '')+f'<h3>{e(label)}</h3><p>{a.get("largura","?")} × {a.get("altura","?")} px · {e(a.get("formato_real","SVG"))} · {a["bytes"]/1024:.0f} KB</p><p>{e(context or "Sem associação principal confirmada")}</p><a href="{e(a["organizado"])}">Abrir arquivo</a>'+(f' · <a href="{e(a["texto_arquivo"])}">Texto OCR</a>' if a.get('texto_arquivo') else '')+'</div></article>'
    content+='</div></main>'+search_script
    (DEST/'imagens.html').write_text(shell('Imagens',content),encoding='utf-8')
    docs=[a for a in assets if a['tipo']=='documento']
    content=header('Documentos e relatórios','Todos os PDFs baixados, com nomes legíveis, número de páginas, origem e texto pesquisável. O OCR não substitui a conferência do documento.')+'<main>'+toolbar([a['grupo'] for a in docs])+'<div class="cards">'
    for a in docs:
        query=base.norm(a['asset_id']+' '+a['titulo']+' '+a['grupo'])
        content+=f'<article class="card" data-card data-group="{e(a["grupo"])}" data-search="{e(query)}"><a href="{e(a["organizado"])}"><img loading="lazy" src="{e(a["miniatura"])}" alt="Primeira página de {e(a["titulo"])}"></a><div class="card-body"><span class="tag">{a["asset_id"]}</span><h3>{e(a["titulo"])}</h3><p>{a["numero_paginas"]} páginas · {a["bytes"]/1000000:.2f} MB · {a.get("paginas_ocr",0)} páginas com OCR</p><a href="{e(a["organizado"])}">Abrir PDF</a> · <a href="{e(a["texto_arquivo"])}">Ler texto</a><p class="small">{e(a["grupo"])}</p></div></article>'
    content+='</div></main>'+search_script
    (DEST/'documentos.html').write_text(shell('Documentos',content),encoding='utf-8')
    content=header('Vídeos','Os arquivos MP4 abaixo estão disponíveis localmente. As referências externas conservam título, duração e endereço, mas não incluem o vídeo completo.')+'<main><h2>Arquivos locais</h2><div class="cards">'
    for a in [a for a in assets if a['tipo']=='video']:
        content+=f'<article class="card"><video controls preload="none" poster="{e(a.get("miniatura",""))}" src="{e(a["organizado"])}"></video><div class="card-body"><span class="tag">{a["asset_id"]}</span><h3>{e(a["titulo"])}</h3><p>{a["duracao"]} · {a.get("largura","?")} × {a.get("altura","?")} · {a["bytes"]/1000000:.1f} MB</p><a href="{e(a["organizado"])}">Abrir MP4</a><p>Áudio preservado, sem transcrição. Identificação pelo contexto da página e quadros de prévia.</p></div></article>'
    content+='</div><h2>Referências externas</h2><div class="scroll-table"><table><thead><tr><th>Título</th><th>Duração declarada</th><th>Disponibilidade</th></tr></thead><tbody>'
    for a in data['videos_externos']:
        content+=f'<tr><td><a href="{e(a["url"])}" target="_blank" rel="noopener noreferrer">{e(a["titulo"])}</a><p class="small">{e(a.get("descricao", "")[:350])}</p></td><td>{e(a["duracao_declarada"])}</td><td>Referência externa; vídeo não baixado</td></tr>'
    content+='</tbody></table></div></main>'
    (DEST/'videos.html').write_text(shell('Vídeos',content),encoding='utf-8')
    content=header('Páginas e textos','Fichas de consulta com texto principal limpo, mídia associada e links públicos. Páginas com conteúdo escasso ou dependente de aplicativos estão identificadas.')+'<main>'+toolbar([p['tema'] for p in pages])+'<div class="cards">'
    for p in pages:
        query=base.norm(p['id']+' '+p['titulo']+' '+p['tema']+' '+p['texto'])
        content+=f'<article class="card" data-card data-group="{e(p["tema"])}" data-search="{e(query)}"><div class="card-body"><span class="tag">{p["id"]}</span><h3><a href="{e(p["consulta_html"])}">{e(p["titulo"])}</a></h3><p>{e(p["tema"])}</p><p>{len(p["imagens"])} imagens associadas · {len(p["documentos"])} PDFs · {p["caracteres_texto"]} caracteres</p><p>{e(p["status_conteudo"])}</p></div></article>'
    content+='</div></main>'+search_script
    (DEST/'paginas.html').write_text(shell('Páginas',content),encoding='utf-8')
    for p in pages:
        out=DEST/p['consulta_html'];out.parent.mkdir(parents=True,exist_ok=True)
        prefix='../'
        main=f'<header><div class="eyebrow">{p["id"]} · {e(p["tema"])}</div><h1>{e(p["titulo"])}</h1><p><a href="{e(p["url"])}">Página de origem</a> · <a href="../paginas.html">Todas as páginas</a> · <a href="{e(base.relative_href(out,SOURCE/p["origem"]))}">Abrir espelho HTTrack</a></p></header><main><p class="notice">Estado: {e(p["status_conteudo"])}. Os links externos e formulários não são reproduzidos como serviços ativos nesta ficha.</p><h2>Texto principal recuperado</h2><pre>{e(p["texto"])}</pre>'
        representatives={}
        for aid in p['imagens']:
            a=asset_map[aid]
            if a.get('melhor_da_familia'): representatives[a['familia']]=a
        if representatives:
            main+='<h2>Imagens associadas</h2><div class="cards">'
            for a in representatives.values():
                label=a.get('rotulo_editorial') or (a['rotulos'][0] if a['rotulos'] else a['asset_id'])
                main+=f'<article class="card"><a href="../{e(a["organizado"])}"><img loading="lazy" src="../{e(a.get("miniatura",a["organizado"]))}" alt="{e(label)}"></a><div class="card-body"><span class="tag">{a["asset_id"]}</span><h3>{e(label)}</h3></div></article>'
            main+='</div>'
        if p['links']:
            main+='<h2>Links encontrados</h2><div class="scroll-table"><table><thead><tr><th>Rótulo</th><th>Destino</th><th>Cópia local</th></tr></thead><tbody>'
            for link in p['links']:
                a=asset_map.get(link['arquivo_local_id']); local=f'<a href="../{e(a["organizado"])}">{e(a.get("asset_id",a["id"]))}</a>' if a and a['tipo'] in {'imagem','documento','video'} else 'Consultar espelho / referência externa'
                if a and a['tipo']=='pagina': local=f'<a href="../{e(page_map[a["pagina_id"]]["consulta_html"])}">Ficha de consulta</a>'
                main+=f'<tr><td>{e(link["rotulo"])}</td><td><a href="{e(link["url"])}">{e(link["url"])}</a></td><td>{local}</td></tr>'
            main+='</tbody></table></div>'
        main+='</main>'
        out.write_text(shell(p['titulo'],main,prefix),encoding='utf-8')


def update_exports(data):
    base.dump(DATA,data)
    records=data['arquivos']
    fields=['id','asset_id','tipo','grupo','origem','organizado','bytes','sha256','duplicado_de','extensao_original','formato_real','largura','altura','numero_paginas','duracao','titulo','rotulo_editorial','rotulos','paginas','urls','status','status_http']
    base.write_csv(DEST/'08_catalogos/inventario-completo.csv',records,fields)
    base.write_csv(DEST/'08_catalogos/imagens.csv',[a for a in records if a['tipo']=='imagem'],fields+['familia','melhor_da_familia','baixa_resolucao','miniatura','texto_arquivo'])
    base.write_csv(DEST/'08_catalogos/documentos.csv',[a for a in records if a['tipo']=='documento'],fields+['paginas_ocr','caracteres_texto_nativo','caracteres_texto_total','texto_arquivo'])
    base.write_csv(DEST/'08_catalogos/duplicados-exatos.csv',[a for a in records if a['duplicado_de']],['id','origem','sha256','duplicado_de','organizado'])
    base.write_csv(DEST/'08_catalogos/paginas.csv',data['paginas'],['id','titulo','url','origem','consulta_html','texto_arquivo','tema','status_conteudo','caracteres_texto','imagens','documentos','videos_locais'])
    base.write_csv(DEST/'04_videos/videos-externos.csv',data['videos_externos'],['titulo','url','duracao_legivel','duracao_declarada','data_publicacao','descricao','paginas'])


def finalize():
    data=read_data()
    # HTTrack escapou algumas referências duas vezes (%2520); refaz os vínculos.
    for rec in data['arquivos']:
        rec['_path']=SOURCE/rec['origem']
        if rec['tipo'] in {'pagina','html-tecnico','html-erro'}: rec['tipo']='html'
    pages,links,external,_=base.analyze_pages(data['arquivos'])
    data['paginas'],data['links'],data['videos_externos']=pages,links,external
    for page in pages:
        if page['origem']=='www.aaci.org.br/index.html': page['titulo']='Página inicial'
        if page['status_conteudo']=='post_sem_conteudo_confirmado':
            page['titulo']='Post não encontrado: '+Path(page['origem']).stem.replace('-',' ')
    for video in [r for r in data['arquivos'] if r['tipo']=='video']:
        if video['titulo'].startswith('Vídeo AACI'):
            matches=[p for p in pages if base.decode_path(p['url']).rstrip('/')==base.decode_path(video.get('origem_captura','')).rstrip('/')]
            if len(matches)==1: video['titulo']=matches[0]['titulo']
        primary=[p for p in pages if base.decode_path(p['url']).rstrip('/')==base.decode_path(video.get('origem_captura','')).rstrip('/')]
        if primary: video['pagina_principal']=primary[0]['id']
        old=DEST/video['organizado']
        target=DEST/'04_videos/locais'/f"{video['asset_id']}--{base.slug(video['titulo'],85)}{old.suffix}"
        if target!=old:
            if not target.resolve().is_relative_to(DEST.resolve()): raise ValueError('Destino de vídeo fora da coleção')
            old.rename(target);video['organizado']=target.relative_to(DEST).as_posix()
    for page in pages:
        page['videos_referenciados']=page['videos_locais'][:]
        page['videos_locais']=[r['id'] for r in data['arquivos'] if r['tipo']=='video' and r.get('pagina_principal')==page['id']]
    for video in external:
        video['url_tecnica_capturada']=video['url']
        if 'youtube.com/embed/' in video['url']:
            video['url']='https://www.youtube.com/watch?v='+video['url'].split('/embed/')[1].split('?')[0]
        elif 'token=' in video['url']:
            # Links assinados são temporários: a consulta pública usa a página de vídeos.
            video['url']='https://www.aaci.org.br/v%C3%ADdeos'
        duration=re.fullmatch(r'PT(?:(\d+)M)?(?:(\d+)S)?',video['duracao_declarada'])
        if duration: video['duracao_legivel']=f"{int(duration[1] or 0):02}:{int(duration[2] or 0):02}"
    for rec in data['arquivos']:
        rec.pop('_path',None)
        if rec['tipo']=='documento' and rec['rotulos']: rec['titulo']=rec['rotulos'][0]
    curate(data);merge_ocr(data);information(data);render_catalog(data);update_exports(data)
    print(json.dumps(data['estatisticas'],ensure_ascii=False,indent=2))


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--prepare-ocr',action='store_true');args=parser.parse_args()
    if args.prepare_ocr:prepare_ocr()
    else:finalize()
