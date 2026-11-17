from pathlib import Path
source=Path('.tmp/relatorio/reduzido.py').read_text(encoding='utf-8-sig')
start=source.index("pic('logo',240)")
end=source.index("page();p('1 Objetivo",start)
opening='''pic('logo',180)
styles['TitleA'].fontSize=21
styles['TitleA'].leading=25
styles['TitleA'].spaceAfter=12
doc.styles['Title'].font.size=Pt(21)
p('Relatório Técnico do Projeto +Web','TitleA')
p('Identificação do projeto','H2A')
names=['Rúben Israel Esterci de Souza','Naamã Lima ferreira','Angelo Bessa','Vitor Hugo Almeida Carmo','Carlos Eduardo de Paiva Paula','Gustavo Henrique Do Nascimento Gonçalves','Gabriel Alves Valverde','Davi Rossini de Paula Pereira','Vinicius Fontes Nocera','Cláudio Bispo de Almeida Filho','Arthur Esteves Gomes','Rhuan de Souza Leite','Lucas Ribeiro Figueiredo Souza','Angelo Giacomini']
table(['Campo','Dados do projeto'],[
 ('Projeto','+Web'),
 ('Cursos envolvidos','Engenharia de Software, Sistemas de Informação e Marketing'),
 ('Instituição','Associação de Apoio a Crianças e Idosos (AACI)'),
 ('Membros',chr(10).join(names))
],[130,340])

'''
source=source[:start]+opening+source[end:]
source=source.replace("exec(base.split(\"pic('logo',300)\")[0])", "exec(base.split(\"pic('logo',300)\")[0].replace(\"(-1,-1),8)\",\"(-1,-1),5)\").replace(\"escape(x),styles['CellA']\",\"escape(x).replace(chr(10),'<br/>'),styles['CellA']\"))")
source=source.replace('Relatorio_Tecnico_+Web_Reduzido','Relatorio_Tecnico_+Web_Organizado')
import re
source=re.sub(r'\s*\[[123](?:[–-][123])?(?:, seção \d+)?\]', '', source)
ref_start=source.index("p('Fontes e comprovações','H2A')")
ref_end=source.index('def footer_pdf',ref_start)
source=source[:ref_start]+source[ref_end:]
exec(compile(source,'organizado','exec'))
