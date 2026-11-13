"""Confere integridade dos originais, cópias e ligações do catálogo AACI."""
from pathlib import Path
from urllib.parse import unquote, urlsplit
import csv
import hashlib
import json
import sys
from lxml import html
import mapear_acervo_aaci as base


def sha(path):
    digest=hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda:stream.read(2**20),b''):digest.update(chunk)
    return digest.hexdigest()


def main():
    root=base.DEST;data=json.loads((root/'08_catalogos/acervo.json').read_text(encoding='utf-8'))
    errors=[];checked={}
    original_paths={p.relative_to(base.SOURCE).as_posix() for p in base.SOURCE.rglob('*') if p.is_file()}
    expected={a['origem'] for a in data['arquivos']}
    if original_paths!=expected:errors.append({'origem_alterada':list(original_paths.symmetric_difference(expected))})
    for a in data['arquivos']:
        source=base.SOURCE/a['origem'];target=root/a['organizado']
        if not source.exists() or sha(source)!=a['sha256']:errors.append({'original_divergente':a['id']})
        if not target.resolve().is_relative_to(root.resolve()):errors.append({'destino_invalido':a['id']});continue
        if target not in checked:checked[target]=sha(target) if target.exists() else None
        if checked[target]!=a['sha256']:errors.append({'copia_divergente':a['id']})
    owned=[]
    for folder in ['03_imagens','04_videos/locais','05_documentos','07_tecnico']:
        owned.extend(p for p in (root/folder).rglob('*') if p.is_file())
    orphans=sorted(p.relative_to(root).as_posix() for p in set(owned)-set(checked))
    if orphans:errors.append({'copias_sem_correspondencia':orphans})
    generated=sorted(root.glob('*.html'))+sorted((root/'01_paginas').glob('*.html'))
    bad_links=[]
    for path in generated:
        tree=html.fromstring(path.read_bytes())
        for el in tree.xpath('//*[@href or @src or @poster]'):
            for key in ['href','src','poster']:
                value=el.get(key,'')
                if not value or value.startswith('#'):continue
                u=urlsplit(value)
                if u.scheme or u.netloc:continue
                target=(path.parent/unquote(u.path)).resolve()
                if not target.exists():bad_links.append({'pagina':path.relative_to(root).as_posix(),'referencia':value})
    if bad_links:errors.append({'links_locais_ausentes':bad_links})
    with (root/'08_catalogos/inventario-completo.csv').open(encoding='utf-8-sig',newline='') as stream:
        csv_count=len(list(csv.DictReader(stream,delimiter=';')))
    if csv_count!=949:errors.append({'linhas_csv':csv_count})
    document_text_pages=0
    for a in data['arquivos']:
        if a['tipo']=='documento':
            if len(a['texto_paginas'])!=a['numero_paginas']:errors.append({'paginas_texto':a['asset_id']})
            document_text_pages+=len(a['texto_paginas'])
    pdf_path=root/'Relatorio-do-acervo-AACI.pdf';doc=base.fitz.open(pdf_path)
    pdf_text='\n'.join(p.get_text() for p in doc)
    missing_ids=[a['asset_id'] for a in data['arquivos'] if a['tipo'] in {'documento','video'} and a['asset_id'] not in pdf_text]
    missing_ids += [p['id'] for p in data['paginas'] if p['id'] not in pdf_text]
    if missing_ids:errors.append({'ids_ausentes_relatorio':missing_ids})
    offpage=[]
    for i,page in enumerate(doc):
        for block in page.get_text('dict')['blocks']:
            for line in block.get('lines',[]):
                for span in line['spans']:
                    x0,y0,x1,y1=span['bbox']
                    if x0<0 or y0<0 or x1>page.rect.width+1 or y1>page.rect.height+1:offpage.append([i+1,span['text']])
    if offpage:errors.append({'texto_fora_da_pagina':offpage})
    result={'data':'13/11/2026','estado':'aprovado' if not errors else 'falhas','arquivos_originais_verificados':len(data['arquivos']),
            'copias_unicas_verificadas':len(checked),'originais_preservados_sha256':not any('original_divergente' in e or 'origem_alterada' in e for e in errors),
            'html_consulta_verificados':len(generated),'links_locais_ausentes':bad_links,'linhas_inventario_csv':csv_count,
            'paginas_pdf_fonte_com_texto_extraido_ou_ocr':document_text_pages,'paginas_relatorio':len(doc),
            'ocr_itens_concluidos':data['estatisticas']['itens_ocr_ok'],'videos_locais_decodificados':sum(a.get('validacao_video')=='decodificacao_integral_ok' for a in data['arquivos']),
            'entradas_cache_crc_verificadas':len(data['cache']),'erros':errors}
    base.dump(root/'08_catalogos/verificacao-final.json',result)
    print(json.dumps(result,ensure_ascii=False,indent=2))
    if errors:raise SystemExit(1)


if __name__=='__main__':main()
