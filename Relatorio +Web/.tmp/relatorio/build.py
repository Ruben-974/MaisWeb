from pathlib import Path
from xml.sax.saxutils import escape
from PIL import Image as PILImage
from docx import Document
from docx.shared import Cm, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, PageBreak, Table, TableStyle, KeepTogether
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY

ROOT=Path.cwd(); OUT=ROOT/'output'; TMP=ROOT/'.tmp/relatorio'
assets={
 'logo':Path('C:/Users/RBENIS~1/AppData/Local/Temp/codex-clipboard-afb2ecbd-8b52-4a08-8f1c-8d8f3c46c37a.png'),
 'antes':Path('C:/Users/RBENIS~1/AppData/Local/Temp/codex-clipboard-a17f56e3-7459-40d2-b717-a633c4785ec7.png'),
 'depois':Path('C:/Users/RBENIS~1/AppData/Local/Temp/codex-clipboard-de3168f3-e4cc-4878-9f80-531c608632d7.png'),
 'visita1':ROOT/'visita 1.jpeg', 'visita2':ROOT/'visita 2.jpeg'}
for key,p in list(assets.items()):
 dest=TMP/(key+p.suffix); dest.write_bytes(p.read_bytes()); assets[key]=dest
pdfmetrics.registerFont(TTFont('Arial','C:/Windows/Fonts/arial.ttf'))
pdfmetrics.registerFont(TTFont('Arial-Bold','C:/Windows/Fonts/arialbd.ttf'))
pdfmetrics.registerFontFamily('Arial',normal='Arial',bold='Arial-Bold',italic='Arial',boldItalic='Arial-Bold')
styles=getSampleStyleSheet()
styles.add(ParagraphStyle(name='BodyA',fontName='Arial',fontSize=10.5,leading=15.5,spaceAfter=9,alignment=TA_JUSTIFY))
styles.add(ParagraphStyle(name='H1A',fontName='Arial-Bold',fontSize=17,leading=21,spaceAfter=15))
styles.add(ParagraphStyle(name='H2A',fontName='Arial-Bold',fontSize=11.5,leading=16,spaceBefore=9,spaceAfter=7))
styles.add(ParagraphStyle(name='CaptionA',fontName='Arial',fontSize=9,leading=12,spaceAfter=10,textColor=colors.HexColor('#444444')))
styles.add(ParagraphStyle(name='CenterA',fontName='Arial',fontSize=11,leading=17,alignment=TA_CENTER,spaceAfter=10))
styles.add(ParagraphStyle(name='TitleA',fontName='Arial-Bold',fontSize=27,leading=34,alignment=TA_CENTER,spaceAfter=20))
styles.add(ParagraphStyle(name='CellA',fontName='Arial',fontSize=9,leading=12))
doc=Document(); sec=doc.sections[0]
sec.page_width=Cm(21);sec.page_height=Cm(29.7)
sec.top_margin=Cm(2);sec.bottom_margin=Cm(2);sec.left_margin=Cm(2.2);sec.right_margin=Cm(2.2)
sec.different_first_page_header_footer=True
for name in ['Normal','Title','Heading 1','Heading 2','Caption']:
 st=doc.styles[name];st.font.name='Arial';st.font.color.rgb=RGBColor(0,0,0)
doc.styles['Normal'].font.size=Pt(10.5)
doc.styles['Normal'].paragraph_format.line_spacing=1.25
doc.styles['Normal'].paragraph_format.space_after=Pt(9)
doc.styles['Heading 1'].font.size=Pt(17);doc.styles['Heading 2'].font.size=Pt(11.5)
doc.styles['Title'].font.size=Pt(27)
doc.styles['Caption'].font.size=Pt(9)
footer=sec.footer.paragraphs[0];footer.alignment=WD_ALIGN_PARAGRAPH.RIGHT
r=footer.add_run('+Web  |  Relatório técnico  |  ');r.font.size=Pt(8)
fld=OxmlElement('w:fldSimple');fld.set(qn('w:instr'),'PAGE');footer._p.append(fld)
doc.core_properties.title='Relatório Técnico do Projeto +Web'
doc.core_properties.author='Equipe +Web | UniAcademia'
story=[]
def p(text,style='BodyA'):
 story.append(Paragraph(escape(text),styles[style]))
 ws={'H1A':'Heading 1','H2A':'Heading 2','CaptionA':'Caption','TitleA':'Title'}.get(style,'Normal')
 para=doc.add_paragraph(text,ws)
 if style in ['CenterA','TitleA']:para.alignment=WD_ALIGN_PARAGRAPH.CENTER
 if style=='BodyA':para.alignment=WD_ALIGN_PARAGRAPH.JUSTIFY
 return para
def space(pt):
 story.append(Spacer(1,pt));pa=doc.add_paragraph();pa.paragraph_format.space_after=Pt(0);pa.paragraph_format.line_spacing=1;pa.add_run().font.size=Pt(pt)
def page():story.append(PageBreak());doc.add_page_break()
def pic(key,width,caption=None):
 path=assets[key];im=PILImage.open(path);h=width*im.height/im.width
 story.append(Image(str(path),width=width,height=h));story.append(Spacer(1,7))
 pa=doc.add_paragraph();pa.alignment=WD_ALIGN_PARAGRAPH.CENTER;pa.paragraph_format.space_after=Pt(5)
 pa.add_run().add_picture(str(path),width=Pt(width))
 if caption:p(caption,'CaptionA')
def table(headers,rows,widths):
 data=[[Paragraph('<b>'+escape(x)+'</b>',styles['CellA']) for x in headers]]+[[Paragraph(escape(x),styles['CellA']) for x in row] for row in rows]
 t=Table(data,colWidths=widths,repeatRows=1,hAlign='LEFT');t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#E3EDF2')),('GRID',(0,0),(-1,-1),.5,colors.HexColor('#D9D9D9')),('VALIGN',(0,0),(-1,-1),'MIDDLE'),('LEFTPADDING',(0,0),(-1,-1),8),('RIGHTPADDING',(0,0),(-1,-1),8),('TOPPADDING',(0,0),(-1,-1),8),('BOTTOMPADDING',(0,0),(-1,-1),8)]));story.append(t);story.append(Spacer(1,10))
 t=doc.add_table(rows=1, cols=len(headers));t.autofit=False
 for c,w,h in zip(t.columns,widths,headers):c.width=Pt(w)
 for c,h in zip(t.rows[0].cells,headers):c.text=h
 for row in rows:
  for c,v in zip(t.add_row().cells,row):c.text=v
 for i,row in enumerate(t.rows):
  for c,w in zip(row.cells,widths):
   c.width=Pt(w)
   pr=c._tc.get_or_add_tcPr();b=OxmlElement('w:tcBorders')
   for side in ['top','left','bottom','right']:
    el=OxmlElement('w:'+side);el.set(qn('w:val'),'single');el.set(qn('w:sz'),'4');el.set(qn('w:color'),'D9D9D9');b.append(el)
   pr.append(b)
   if i==0:
    sh=OxmlElement('w:shd');sh.set(qn('w:fill'),'E3EDF2');pr.append(sh)
   for pa in c.paragraphs:
    pa.paragraph_format.space_before=Pt(4);pa.paragraph_format.space_after=Pt(4);pa.paragraph_format.line_spacing=1.1
    for r in pa.runs:r.font.size=Pt(9);r.bold=i==0
  trpr=row._tr.get_or_add_trPr();trpr.append(OxmlElement('w:cantSplit'))
 doc.add_paragraph().paragraph_format.space_after=Pt(0)

pic('logo',300)
space(65)
p('Relatório Técnico do Projeto +Web','TitleA')
p('Desenvolvimento do website institucional da AACI','CenterA')
space(26)
p('Associação de Apoio a Crianças e Idosos','CenterA')
p('Projeto de extensão universitária','CenterA')
p('Engenharia de Software • Sistemas de Informação • Marketing','CenterA')
space(100)
p('UniAcademia Centro Universitário','CenterA')
p('Juiz de Fora — MG','CenterA')
p('16 de novembro de 2026','CenterA')

page();p('Equipe do projeto','H1A')
names=['Rúben Israel Esterci de Souza','Naamã Lima ferreira','Angelo Bessa','Vitor Hugo Almeida Carmo','Carlos Eduardo de Paiva Paula','Gustavo Henrique Do Nascimento Gonçalves','Gabriel Alves Valverde','Davi Rossini de Paula Pereira','Vinicius Fontes Nocera','Cláudio Bispo de Almeida Filho','Arthur Esteves Gomes','Rhuan de Souza Leite','Lucas Ribeiro Figueiredo Souza','Angelo Giacomini']
for n in names:
 pa=p(n,'CenterA');pa.paragraph_format.space_after=Pt(4)
p('Coordenação do grupo: Rúben Israel Esterci de Souza.','CaptionA')
p('Sumário','H2A')
for line in ['1 Apresentação e metodologia ........................................ 3','2 Etapas e atividades desenvolvidas ................................ 4','3 Primeira visita técnica .................................................. 5','4 Segunda visita técnica .................................................. 6','5 Desenvolvimento técnico .............................................. 7','6 Comparação visual do site ............................................ 8','7 Análise das alterações .................................................. 9','8 Resultados e continuidade .......................................... 10','9 Referências e comprovações ...................................... 11']:
 p(line,'CaptionA')

page();p('1 Apresentação e metodologia','H1A')
p('O +Web é um projeto de extensão do UniAcademia voltado à reorganização da presença digital da Associação de Apoio a Crianças e Idosos (AACI), em Juiz de Fora. O trabalho reuniu levantamento de necessidades, aproximação presencial, prototipação, organização de conteúdo e desenvolvimento de uma versão navegável do website institucional. Até 16 de novembro de 2026, o projeto apresentava entregas técnicas e retorno favorável da instituição, com ajustes de conteúdo e formalização da entrega ainda em andamento. [1–3]')
p('Contexto e objetivos','H2A')
p('Na reunião de maio, a AACI apresentou seus serviços de convivência e fortalecimento de vínculos para crianças e adolescentes de 6 a 14 anos, atividades com idosos e apoio à comunidade. A instituição já possuía um website com informações abrangentes, mas apontou excesso de páginas, conteúdos redundantes e necessidade de melhorar a apresentação das formas de contribuição. [1]')
p('O objetivo geral foi desenvolver uma nova organização do website, facilitando o acesso às informações institucionais e às formas de apoio. Os objetivos específicos abrangeram reorganizar a navegação, valorizar os serviços sociais, reunir conteúdos de transparência, destacar doações e contato e adequar textos e imagens à realidade da AACI. [1–2]')
p('Metodologia aplicada','H2A')
p('O processo foi organizado em ciclos de levantamento, proposta, avaliação e adequação. As reuniões com a AACI permitiram identificar necessidades e prioridades; as visitas aproximaram a equipe do contexto institucional; o protótipo traduziu os requisitos em uma proposta visual; e o retorno da instituição orientou a seleção de conteúdos e a implementação. As atas registraram decisões e encaminhamentos, enquanto o mapeamento das páginas existentes apoiou a reorganização do conteúdo. [1–3]')
p('O primeiro semestre concentrou planejamento, requisitos e documentação. No segundo semestre, a equipe retomou o contato, elaborou o protótipo, apresentou a proposta presencialmente e avançou para a implementação. A comunicação contínua apoiou o compartilhamento de materiais e o acompanhamento dos ajustes. Essa sequência caracteriza uma condução iterativa com participação da instituição beneficiada. [1–3]')
p('A verificação dos resultados distingue as entregas documentadas, os recursos descritos na documentação técnica e as funcionalidades previstas para continuidade. A comparação visual das páginas iniciais evidencia mudanças de apresentação; métricas de acesso, conversão ou impacto social exigem avaliação específica. [3–6]')

page();p('2 Etapas e atividades desenvolvidas','H1A')
table(['Período','Atividades e encaminhamentos'],[
 ('Março e abril de 2026','Formação da equipe, organização acadêmica e prospecção de instituições. Primeiro contato com a AACI em 08/04, seguido de esclarecimento do escopo e negociação de agenda.'),
 ('04/05/2026','Reunião remota de requisitos às 16h45. Priorização de doações, navegação, atualização de conteúdo e atendimento. Definição das etapas de planejamento e implementação.'),
 ('Maio e junho de 2026','Redação e circulação da ata, visita de 21/05, definição do nome +Web, propostas de identidade visual e organização das frentes de trabalho.'),
 ('Agosto e setembro de 2026','Retomada da equipe e do contato institucional. Decisão de prototipar com o conteúdo disponível, reunião interna e elaboração da proposta da página inicial.'),
 ('Outubro de 2026','Envio do protótipo em 01/10 e reunião presencial em 21/10. Discussão de serviços, transparência, mídias e adequação dos conteúdos. Recebimento de materiais institucionais.'),
 ('Novembro de 2026','Mapeamento das páginas, compartilhamento de versão navegável, continuidade da implementação e retorno institucional em 13/11, com solicitações de ajustes.')
],[100,370])
p('Levantamento de requisitos','H2A')
p('A primeira ata definiu como prioridade a captação de doações. Foram discutidos valores sugeridos e livres e a associação das contribuições a exemplos de apoio. Também foram solicitadas revisão das abas, remoção de conteúdo desatualizado, destaque às notícias e melhoria dos canais de recrutamento e atendimento. Esses itens estabeleceram o escopo inicial, sem significar que todas as funcionalidades foram concluídas. [1]')
p('Organização do trabalho','H2A')
p('A equipe planejou frentes de requisitos, interface e desenvolvimento. O relatório geral registra atividades de coordenação, comunicação com a AACI, prototipação, mapeamento e integração do website. A documentação das decisões e os arquivos entregues permitiram acompanhar o avanço entre os semestres. [3, seções 3–6 e 9]')

page();p('3 Primeira visita técnica','H1A')
p('A visita de 21 de maio de 2026 deu continuidade ao alinhamento remoto de 4 de maio e à proposta de conhecer a operação da AACI. O encontro aproximou o grupo do espaço institucional e forneceu contexto para a organização do website. O relatório geral registra mensagens sobre deslocamento, chegada e agradecimentos, além do envio posterior da fotografia pela instituição, em 25 de maio. [1; 3, seção 4]')
pic('visita1',405,'Figura 1 — Registro da primeira visita à AACI. Visita contextualizada em 21/05/2026 pelo relatório geral. Fonte: fotografia “visita 1.jpeg” e registro fotográfico de maio descrito em [3].')
p('Contribuição para o projeto','H2A')
p('A aproximação presencial complementou o levantamento inicial e ajudou a situar as necessidades digitais na rotina da instituição. A síntese posterior citada no relatório geral aborda restrições de acesso e horários dos públicos atendidos e questões técnicas discutidas pelo grupo. A fotografia documenta o encontro, sem atribuição nominal de presença por reconhecimento visual. [3, atividades AT26–AT29]')

page();p('4 Segunda visita técnica','H1A')
p('Em 21 de outubro de 2026, às 9h15, ocorreu a reunião presencial de apresentação do protótipo na sede da AACI, em Benfica, Juiz de Fora. A ata principal registra Rúben Israel Esterci de Souza, Arthur Esteves Gomes e Rhuan de Souza Leite como participantes do grupo acadêmico. A proposta foi avaliada positivamente pela instituição, que destacou a organização visual e indicou a necessidade de adequar e complementar os conteúdos. [2]')
pic('visita2',430,'Figura 2 — Registro fotográfico fornecido como segunda visita à AACI. Fonte: fotografia “visita 2.jpeg”. O encontro de apresentação do protótipo está documentado na ata de 21/10/2026. [2]')
p('Decisões e encaminhamentos','H2A')
p('A discussão reforçou o destaque às atividades com idosos, a apresentação dos projetos sociais, a manutenção de documentos de transparência e o uso de fotografias, vídeos e depoimentos. A AACI ficou responsável por selecionar informações prioritárias e compartilhar materiais; o grupo acadêmico, por organizar esse conteúdo e dar continuidade ao desenvolvimento. [2]')
p('O chatbot foi mantido como possibilidade para 2027, condicionada ao alinhamento acadêmico e à continuidade da parceria. A consolidação dos nomes e das assinaturas da segunda ata permanecia pendente no corte do relatório geral. [2–3]')

page();p('5 Desenvolvimento técnico','H1A')
p('Prototipação e arquitetura da informação','H2A')
p('A equipe decidiu, em setembro, desenvolver o protótipo com os dados disponíveis e colher o retorno institucional na sequência. O PDF encaminhado à AACI em 1º de outubro apresentou a estrutura base da página inicial. Os conteúdos demonstrativos dessa etapa orientavam a composição visual e precisavam de adequação antes da utilização definitiva. A reunião de outubro permitiu revisar a proposta com a instituição. [2–3]')
p('O desenho contemplou apresentação institucional, serviços sociais, formas de contribuição, depoimentos, patrocinadores, transparência, vídeos e perguntas frequentes. A reorganização procurou tornar os principais caminhos mais claros e reduzir a dispersão identificada na primeira reunião. [1–2]')
p('Mapeamento e preparação de conteúdo','H2A')
p('Em novembro, foram organizadas tarefas de levantamento de páginas, textos, links e imagens do site existente. O relatório geral identifica cinco pacotes de mapeamento: Depoimentos, de Angelo Giacomini; Política de Privacidade, de Gustavo Henrique; mapa estrutural, de Arthur; Telemarketing, de Naamã; e Notícias, de Cláudio. Também registra declarações de entrega de Contato e Como Ajudar, sem os respectivos arquivos no acervo então analisado. [3, seção 6]')
p('Implementação e recursos documentados','H2A')
p('Segundo a análise técnica registrada no relatório geral, a implementação local reunia 20 páginas HTML e recursos de serviços, notícias, contato e transparência. O fluxo de doação incluía modal, Pix com valor e QR Code; a documentação descrevia biblioteca com 26 PDFs e encaminhamento de contato pelo WhatsApp. O cadastro integrado de currículos e voluntários não estava comprovado como entrega. [3, seção 8]')
p('Validação e revisão','H2A')
p('O relatório geral descreve registros preexistentes de validação estrutural das 20 páginas, testes de interação em ambiente simulado, verificações de layout nas larguras de 320, 375, 768, 950 e 1440 pixels e decodificação de nove QR Codes. Esses resultados são registros documentais da implementação e não equivalem a testes bancários, auditoria integral de acessibilidade ou validação em aparelhos físicos. [3, seção 8]')
p('Em 13 de novembro, o retorno da AACI foi favorável à versão navegável, com pedidos de substituição de duas fotografias e retirada de contatos de apadrinhamento afetivo. A seleção final de mídias e a revisão dos dados institucionais integraram a etapa de adequação anterior à entrega. [3, atividade AT65]')

page();p('6 Comparação visual do site','H1A')
p('As capturas apresentam a página inicial anterior e a versão reformulada, permitindo comparar a organização do cabeçalho, a mensagem principal e os caminhos de apoio. O “depois” representa o estado visual apresentado, sem implicar aceite final ou migração para o domínio institucional. [3; 6]')
p('Antes','H2A');pic('antes',445,'Figura 3 — Página inicial anterior da AACI. Menu distribuído em linhas, imagem central e apresentação institucional em texto. Fonte: captura fornecida para este relatório. [6]')
p('Depois','H2A');pic('depois',445,'Figura 4 — Página inicial reformulada. Navegação reorganizada, chamada principal, destaque à doação e início da seção de serviços. Fonte: captura fornecida para este relatório. [6]')
p('O valor de R$ 50 e a referência a materiais escolares são elementos exibidos na interface. A captura demonstra a forma de apresentação do apoio; não constitui comprovação de custo, doação recebida ou benefício efetivamente entregue pelo projeto. [3; 6]','CaptionA')

page();p('7 Análise das alterações','H1A')
table(['Aspecto','Versão anterior','Versão reformulada'],[
 ('Navegação','Menu com muitos destinos distribuídos em três linhas na captura.','Menu principal em uma linha, agrupamentos e botão “Quero doar” destacado.'),
 ('Mensagem inicial','Apresentação institucional em parágrafo ao lado da marca, sobre a composição fotográfica.','Título de maior destaque e mensagem orientada à contribuição e à atuação social.'),
 ('Doações','“Como Ajudar” aparece como item do menu; não há chamada de doação em destaque no trecho inicial capturado.','Botão no cabeçalho e cartão de contribuição com valor sugerido e exemplo de destinação.'),
 ('Serviços','O trecho capturado prioriza a apresentação institucional.','A seção “O que fazemos” aparece logo após o bloco principal.'),
 ('Transparência','“Prestação de Contas” aparece em uma linha inferior do menu.','“Transparência” aparece na navegação principal e como atributo no bloco de apresentação.'),
 ('Contato','Acesso por “Contato” no menu.','Acesso por “Contato” e botão flutuante com símbolo do WhatsApp.'),
 ('Composição visual','Imagem central com margens laterais amplas e texto institucional de menor destaque.','Imagem em largura ampla, texto em painel claro e botões com maior contraste visual.')
],[80,195,195])
p('Relação com os requisitos','H2A')
p('As mudanças visíveis respondem às prioridades da primeira reunião: reorganização da navegação e maior destaque à captação de doações. O posicionamento dos serviços e da transparência também corresponde aos temas reforçados em outubro. A comparação sustenta uma mudança de hierarquia visual e de exposição dos caminhos principais. [1–2; 6]')
p('A legibilidade, a facilidade de uso e o alcance das chamadas devem ser avaliados com usuários e métricas de operação. Não se deduzem aumento de doações, maior tráfego, desempenho ou conformidade integral de acessibilidade apenas a partir das capturas. [3; 6]')

page();p('8 Resultados e continuidade','H1A')
p('Resultados alcançados','H2A')
p('O trabalho consolidou a aproximação entre a equipe acadêmica e a AACI, o levantamento das necessidades do website, duas reuniões formais registradas em ata e uma visita adicional em maio. Produziu também proposta visual, mapeamento de conteúdos e uma versão navegável, acompanhada por retorno institucional favorável. As fotografias e as capturas apresentadas neste relatório complementam a documentação dessas etapas. [1–6]')
p('O avanço técnico mais evidente foi a transformação dos requisitos em uma interface com navegação reorganizada, destaque às formas de apoio e apresentação dos serviços. A implementação descrita no relatório geral ampliou essa proposta para páginas internas, conteúdo institucional, documentos e recursos de contato e doação. A demonstração dessas entregas deve ser separada da operação definitiva do site. [3; 6]')
p('Acompanhamento das pendências','H2A')
table(['Frente','Encaminhamento'],[
 ('Conteúdo e imagens','Concluir a revisão das fotografias, contatos, endereço e demais informações com a AACI, incluindo os ajustes solicitados em 13/11.'),
 ('Documentação','Consolidar a versão da segunda ata, confirmar os nomes institucionais e recolher as assinaturas pertinentes.'),
 ('Entrega técnica','Registrar o aceite final, a entrega dos arquivos e acessos e a situação de domínio e hospedagem.'),
 ('Continuidade','Avaliar o chatbot e ferramentas de cadastro de voluntários em etapa posterior, conforme disponibilidade acadêmica e prioridades da instituição.')
],[110,360])
p('Considerações finais','H2A')
p('O +Web aplicou conhecimentos de tecnologia e comunicação a uma demanda concreta de uma instituição social. A combinação de reuniões, visitas, prototipação e organização de conteúdo permitiu avançar do diagnóstico para uma solução navegável. O processo também evidenciou a importância de registrar decisões, definir responsáveis e validar textos e imagens com a instituição. [1–3]')
p('A continuidade deve concentrar-se na conclusão dos ajustes, na formalização da entrega e no acompanhamento da utilização do website. A avaliação posterior de acessos, uso dos canais de contato e contribuições poderá indicar os efeitos da solução, sem atribuir ao projeto resultados sociais ou financeiros ainda não medidos. [3]')

page();p('9 Referências e comprovações','H1A')
p('Fontes documentais','H2A')
p('[1] ATA DE REUNIÃO 01 (Aaci). Reunião de alinhamento do projeto de extensão, realizada remotamente em 04/05/2026, às 16h45. Documento principal com quatro páginas. Fundamenta contexto, necessidades, prioridades e divisão das fases do projeto.')
p('[2] ATA DE REUNIÃO 02 (Aaci). Reunião de alinhamento realizada presencialmente em 21/10/2026, às 9h15. Documento principal com quatro páginas. Fundamenta apresentação do protótipo, avaliação institucional, adequação dos conteúdos e próximos passos.')
p('[3] Relatorio Geral.pdf. Relatório geral do projeto para a AACI, versão documental de 16/11/2026, com 25 páginas. Fundamenta a cronologia dos semestres, a visita de maio, as atividades de mapeamento, a situação técnica, o retorno institucional e as pendências. As menções à implementação e aos testes neste relatório remetem à seção 8 dessa fonte.')
p('Registros visuais','H2A')
p('[4] visita 1.jpeg. Fotografia fornecida da primeira visita à AACI, reproduzida na Figura 1. A visita de maio e o envio de fotografia pela AACI em 25/05 estão contextualizados no relatório geral.')
p('[5] visita 2.jpeg. Fotografia fornecida como registro da segunda visita à AACI, reproduzida na Figura 2. A atividade de apresentação do protótipo é descrita na ata de outubro.')
p('[6] Capturas de tela fornecidas das versões anterior e reformulada do website da AACI. Reproduzidas nas Figuras 3 e 4 e utilizadas na comparação visual. Não possuem data de captura indicada.')
p('[7] UniAcademia Centro Universitário. Logotipo fornecido para identificação institucional na capa.')
p('Relação entre entregas e evidências','H2A')
table(['Entrega ou atividade','Comprovação principal'],[
 ('Requisitos e planejamento','Ata de 04/05/2026 [1].'),
 ('Visita de maio','Relatório geral e fotografia da primeira visita [3–4].'),
 ('Apresentação presencial do protótipo','Ata de 21/10/2026 e registro da segunda visita [2; 5].'),
 ('Mapeamento e implementação','Seções 6 e 8 do relatório geral [3].'),
 ('Reformulação visual','Capturas comparativas da página inicial [6].'),
 ('Retorno institucional e ajustes','Atividade AT65 e pendências no relatório geral [3].')
],[200,270])

def footer_pdf(canvas,document):
 if document.page>1:
  canvas.setFont('Arial',8);canvas.setFillColor(colors.HexColor('#555555'))
  canvas.drawRightString(533,32,f'+Web  |  Relatório técnico  |  {document.page}')
doc.save(OUT/'Relatorio_Tecnico_+Web.docx')
SimpleDocTemplate(str(OUT/'Relatorio_Tecnico_+Web.pdf'),pagesize=(595.276,841.89),leftMargin=62.36,rightMargin=62.36,topMargin=56.69,bottomMargin=56.69,title='Relatório Técnico do Projeto +Web',author='Equipe +Web | UniAcademia').build(story,onFirstPage=footer_pdf,onLaterPages=footer_pdf)
print('Criados DOCX e PDF')

