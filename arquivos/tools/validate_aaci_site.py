"""Valida ligações, estrutura e integridade dos recursos do site principal."""
from collections import Counter
from pathlib import Path
from urllib.parse import unquote, urlsplit
import hashlib
import json
from lxml import html

SUPPORT=Path(__file__).resolve().parents[1]
ROOT=SUPPORT.parent/'AACI'
DATA=SUPPORT/'dados'


def digest(path):
 h=hashlib.sha256()
 with path.open('rb') as stream:
  for part in iter(lambda:stream.read(2**20),b''):h.update(part)
 return h.hexdigest()


def main():
 pages=json.loads((DATA/'site-pages.json').read_text(encoding='utf-8'))['paginas']
 errors=[];yt=Counter();html_count=0
 for name in pages:
  path=ROOT/name;raw=path.read_text(encoding='utf-8');tree=html.fromstring(raw);ids=tree.xpath('//@id')
  if '\ufffd' in raw:errors.append([name,'encoding replacement character'])
  duplicate=[key for key,count in Counter(ids).items() if count>1]
  if duplicate:errors.append([name,'duplicate IDs',duplicate])
  if len(tree.xpath('//main'))!=1 or len(tree.xpath('//h1'))!=1:errors.append([name,'main / h1 count'])
  for el in tree.xpath('//*[@src or @href or @poster or @data-local-src or @data-local-href or @data-local-poster]'):
   for attr in ['src','href','poster','data-local-src','data-local-href','data-local-poster']:
    value=el.get(attr,'');u=urlsplit(value)
    if not value or u.scheme or u.netloc:continue
    target=(path.parent/unquote(u.path)).resolve() if u.path else path
    if not target.is_relative_to(ROOT):errors.append([name,'reference outside site',value]);continue
    if not target.exists():errors.append([name,'missing local reference',value]);continue
    if u.fragment and target.suffix=='.html':
     t=tree if target==path else html.fromstring(target.read_bytes())
     if not t.xpath('//*[@id=$id]',id=u.fragment):errors.append([name,'missing anchor',value])
  for el in tree.xpath('//*[@aria-controls or @aria-labelledby or @aria-describedby]'):
   for attr in ['aria-controls','aria-labelledby','aria-describedby']:
    for ident in el.get(attr,'').split():
     if ident not in ids:errors.append([name,'missing ARIA reference',ident])
  for el in tree.xpath('//img[@src]'):
   if el.get('alt') is None:errors.append([name,'missing image alt',el.get('src')])
   if not el.get('width') or not el.get('height'):errors.append([name,'missing image dimensions',el.get('src')])
  for el in tree.xpath('//*[@data-youtube]'):yt[el.get('data-youtube')]+=1
  html_count+=1
 docs=json.loads((DATA/'document-map.json').read_text(encoding='utf-8'))['documentos']
 assets=json.loads((DATA/'asset-map.json').read_text(encoding='utf-8'))
 media=list(assets['videos'].values())
 for item in docs+media:
  if digest(ROOT/item['path'])!=item['sha256']:errors.append(['asset hash',item['path']])
 expected={'uDHRizneRKA','lWxUV477eho','qHtH_RGf0Ro','21nHcb3aW1Q','ZWRPjVnhJs0','B2m5VMVNvvg','NBQDaKdFK5c'}
 if set(yt)!=expected:errors.append(['YouTube coverage',list(yt)])
 result={'estado':'aprovado' if not errors else 'falhas','paginas_verificadas':html_count,'documentos_locais_sha256':len(docs),
         'videos_locais_sha256':len(media),'youtube_ids_e_ocorrencias':dict(yt),'erros':errors,
         'teste_de_layout':'Verificação separada: arquivos/tools/test_aaci_layout.cjs; relatório em arquivos/output/site-layout-tests.json.'}
 target=SUPPORT/'output/site-validation.json';target.parent.mkdir(exist_ok=True);target.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
 print(json.dumps(result,ensure_ascii=False,indent=2))
 if errors:raise SystemExit(1)


if __name__=='__main__':main()
