"""Gera documentação editorial e PDF verificável do inventário da AACI."""
from __future__ import annotations
import html
import json
import os
import re
import shutil
import sys
from collections import Counter
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import BaseDocTemplate, Flowable, Frame, Image, KeepTogether, PageBreak, PageTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.platypus.tableofcontents import TableOfContents
import mapear_acervo_aaci as base

DEST, SOURCE, TMP = base.DEST, base.SOURCE, base.TMP
OUTPUT = base.WORKSPACE / 'output/pdf/Relatorio-do-acervo-AACI.pdf'

PAGE_SUMMARY = {
'PAG-001':'Galeria de 2024: Arraiá, Festa da Primavera, Dia das Crianças e Natal Solidário, com links para os registros.',
'PAG-002':'Perguntas frequentes do Apadrinhamento Afetivo: convivência, documentação, habilitação, visitas e desligamento, conforme o texto capturado.',
'PAG-003':'Apresentação do Apadrinhamento Afetivo e do papel de padrinhos e madrinhas na construção de vínculos.',
'PAG-004':'Etapas do processo de apadrinhamento e orientação para o primeiro contato com a equipe técnica.',
'PAG-005':'Página de contato do Apadrinhamento; os dados específicos estão em uma imagem, também lida e catalogada.',
'PAG-006':'Resultados de 2022 do Apadrinhamento: divulgação, acolhida, capacitação, encontros e acompanhamento das aproximações.',
'PAG-007':'Índice de notícias: cozinhas comunitárias, entrega de móveis, mensagens de doação e reportagem de fisioterapia.',
'PAG-008':'Instruções aos colaboradores para cadastro e acesso a holerites pelo Onvio; não há holerites individuais baixados.',
'PAG-009':'Motivos para doar, Pix, dados bancários, voluntariado e canais de contato; também reúne imagens de campanhas.',
'PAG-010':'E-mails, telefones, endereço, redes sociais e formulário de contato da instituição.',
'PAG-011':'Índice de galerias por ano, predominantemente composto de navegação e mídia.',
'PAG-012':'Página de depoimentos com título e elementos gráficos; não foi recuperado depoimento textual no corpo principal.',
'PAG-013':'Estrutura de candidatura: identificação, contatos, informações acadêmicas e profissionais e link de currículo.',
'PAG-014':'Galeria de fotos e vídeos de 2020 e 2021, com texto principal reduzido e conteúdo visual.',
'PAG-015':'Galeria de 2023: Natal, Arraiá e Dia de Cooperar; Páscoa e Carnaval aparecem como “Em breve!”.',
'PAG-016':'Fotografias de Natal de 2020 e 2021, com imagens de entregas, famílias e atividades.',
'PAG-017':'Apresentação geral, serviços, ODS, apoios, vídeos, newsletter e dados de contato no rodapé.',
'PAG-018':'Menu de acesso a parceiros, transparência, fotos e vídeos.',
'PAG-019':'Direção, associados, unidade de Juiz de Fora e gerência de telemarketing, como declarados na captura.',
'PAG-020':'Fotografias das instalações: salas, informática, cozinha, refeitório, brinquedoteca, recepção e espaços de encontro.',
'PAG-021':'Logos das organizações apresentadas como parceiras, preservados como arquivos de imagem.',
'PAG-022':'Política de privacidade: dados tratados, finalidades, compartilhamento, segurança, cookies, direitos e contato.',
'PAG-023':'O HTML informa que o post não foi encontrado. O conteúdo editorial do endereço não foi recuperado.',
'PAG-024':'O HTML informa que o post não foi encontrado. O conteúdo editorial do endereço não foi recuperado.',
'PAG-025':'Notícia de visita a Muriaé e anúncio de gestão de três cozinhas comunitárias; inclui vídeo local.',
'PAG-026':'Campanha contra a insegurança alimentar, com texto de mobilização, chave Pix e vídeo local.',
'PAG-027':'Mensagem audiovisual de agradecimento e apoio à AACI. O texto do post é curto; há MP4 local associado pela origem do HTTrack.',
'PAG-028':'Notícia sobre entrega de móveis a famílias atingidas por enchentes, em parceria com a Ação Cidadania; inclui vídeo local.',
'PAG-029':'Rota de post sem conteúdo editorial recuperado; corpo informa página não encontrada.',
'PAG-030':'Rota de post sem conteúdo editorial recuperado; corpo informa página não encontrada.',
'PAG-031':'Reportagem de 04/07/2024 sobre a sala de fisioterapia e o projeto Viver Bem Mais, com menção a 54 atendimentos gratuitos naquele contexto.',
'PAG-032':'Rota de post sem conteúdo editorial recuperado; corpo informa página não encontrada.',
'PAG-033':'Prestação de contas: oito termos de parceria, despesas próprias, dados de acolhimento e relatório SCFV 2025.',
'PAG-034':'História, missão, visão, valores, público atendido e localização declarada da AACI.',
'PAG-035':'Voluntariado em projetos, oficinas e atividades culturais; fornece e-mails, endereço e telefones.',
'PAG-036':'Descrição do SCFV, público, objetivos, gratuidade e fortalecimento dos vínculos familiares e comunitários.',
'PAG-037':'Rotinas, horários por grupo, orientações para responsáveis e imagens do espaço.',
'PAG-038':'Oficinas, reciclagem, cinema, roda de conversa, datas comemorativas, reuniões de família, psicologia e serviço social.',
'PAG-039':'Contato do SCFV com dados em imagem; os endereços e telefones foram registrados com sua fonte.',
'PAG-040':'Apresentação do SCFV e da Casa de Atenção à Pessoa Idosa: objetivos, públicos, cuidados e apoio às famílias.',
'PAG-041':'Telemarketing filantrópico, processo de captação, perguntas frequentes e canais para solicitações sobre dados e ligações.',
'PAG-042':'Recrutamento, link de vagas, indicação de editais “Em breve!” e acesso à candidatura.',
'PAG-043':'Biblioteca de relatórios, portfólios, estatuto, ata e comprovante de viagem. Seis referências não têm PDF local.',
'PAG-044':'Catálogo de 12 vídeos com títulos, descrições, durações e referências externas de reprodução.',
'PAG-045':'Variante da página de vídeos com item selecionado; foi mantida como ficha distinta e identificada no inventário.',
}

DOC_SUMMARY = {
'DOC-001':'Anexos e demonstrativos de prestação de contas da parceria de Apadrinhamento Afetivo. Inclui receitas, despesas e documentos de suporte.',
'DOC-002':'Prestação de contas do Espaço de Cuidados para Pessoa Idosa, com demonstrativos financeiros e anexos.',
'DOC-003':'Documentação financeira da parceria de acolhimento em Casa de Passagem, vinculada ao termo 05.2022.047.',
'DOC-004':'Prestação de contas do acolhimento emergencial e temporário do Centro, termo 05.2022.048.',
'DOC-005':'Demonstrativos e anexos referentes à Cozinha Comunitária, termo 05.2023.186.',
'DOC-006':'Prestação de contas do acolhimento Norte, termo 05.2023.198. O rótulo do site menciona atendimento por 16 horas e 50 vagas.',
'DOC-007':'Demonstrativos da parceria de Direito à Vida e à Saúde, termo de fomento 06.2023.005.',
'DOC-008':'Digitalizações de demonstrativos de receitas e despesas do SCFV, termo 0627/24; a maior parte demandou OCR.',
'DOC-009':'Ata da Assembleia Geral Extraordinária de 17/09/2025, com deliberações, assinaturas e registros.',
'DOC-010':'Comprovante referente à viagem de 15/05/2024 para entrega de doações ao Rio Grande do Sul, com declarações e recibos.',
'DOC-011':'Tabelas de 2022 do acolhimento emergencial, com registros diários de usuários e pernoites.',
'DOC-012':'Tabelas de 2022 e 2023 da Casa de Passagem Benfica, organizadas por datas e totais mensais.',
'DOC-013':'Relato de aplicação de recursos próprios nas parcerias com Juiz de Fora, com justificativas e registros fotográficos de estrutura e aquisições.',
'DOC-014':'Estatuto social de 17/09/2025: denominação, finalidades, administração, associados, patrimônio e disposições institucionais.',
'DOC-015':'Portfólio de 2020, com proposta temática, apresentação das atividades e registros visuais de ações educativas.',
'DOC-016':'Portfólio de 2019, reunindo apresentação institucional, oficinas, projetos, imagens e apoios.',
'DOC-017':'Relatório anual de execução do SCFV em 2015, com apresentação, atividades, avaliação e registros.',
'DOC-018':'Relatório anual do SCFV em 2016, com contexto de atuação e descrição de atividades e resultados do período.',
'DOC-019':'Relatório anual do SCFV em 2017, com ações socioeducativas e registros da execução.',
'DOC-020':'Relatório anual do SCFV em 2018, com propósito institucional, atividades e avaliação do exercício.',
'DOC-021':'Relatório anual do SCFV em 2019, com ações do ano, apoios e registros de desenvolvimento das atividades.',
'DOC-022':'Relatório do SCFV em 2021, com descrição de atividades, acompanhamento e ações do período.',
'DOC-023':'Relatório de 2023 da Casa de Atenção à Pessoa Idosa, com identificação do serviço, público, cuidados e atividades.',
'DOC-024':'Relatório de atividades de 2022 do Apadrinhamento Afetivo: divulgação, habilitação, capacitações e acompanhamento.',
'DOC-025':'Relatório SCFV 2025, “AACI em Movimento - Arte, Cultura e Convivência”, com identificação, ações, registros e avaliação.',
'DOC-026':'Relatório do SCFV em 2020, com atividades e formas de acompanhamento durante o período da pandemia.',
}

VIDEO_SUMMARY = {
'VID-001':'Registro vertical de visita a uma cozinha comunitária, com equipe, instalações e encerramento com marcas institucionais.',
'VID-002':'Registro vertical de entrega de itens a famílias, com conversa e exibição dos bens doados.',
'VID-003':'Mensagem de uma pessoa atendida, com caixa de doação e texto final de mobilização. O título é recuperado da página de origem.',
'VID-004':'Peça de mobilização contra a fome, com cenas de crianças e alimentação, textos sobre doação e identificação da AACI.',
}


def clean(value):
    return str(value).replace('\u2011','-').replace('\u2013','-').replace('\u2014','-').replace('\u00a0',' ')


def esc(value): return html.escape(clean(value), quote=True)


def fonts():
    folder=Path('C:/Windows/Fonts')
    for name,file in [('AACI','DejaVuSans.ttf'),('AACIBold','DejaVuSans-Bold.ttf'),('AACIItalic','DejaVuSans-Oblique.ttf'),('AACISerif','georgiab.ttf')]:
        pdfmetrics.registerFont(TTFont(name,str(folder/file)))
    pdfmetrics.registerFontFamily('AACI',normal='AACI',bold='AACIBold',italic='AACIItalic',boldItalic='AACIBold')


WINE=colors.HexColor('#64152e'); INK=colors.HexColor('#29252a'); MUTED=colors.HexColor('#6c6269'); LINE=colors.HexColor('#e4d8dc'); CREAM=colors.HexColor('#faf6f3')
STYLES={}


def initialize_styles():
    STYLES.update({
      'body':ParagraphStyle('Body',fontName='AACI',fontSize=9.4,leading=14,textColor=INK,spaceAfter=9),
      'h1':ParagraphStyle('Section',fontName='AACISerif',fontSize=23,leading=29,textColor=WINE,spaceBefore=6,spaceAfter=18,keepWithNext=True),
      'h2':ParagraphStyle('Subsection',fontName='AACIBold',fontSize=12.5,leading=18,textColor=WINE,spaceBefore=15,spaceAfter=9,keepWithNext=True),
      'small':ParagraphStyle('Small',fontName='AACI',fontSize=7.6,leading=11,textColor=MUTED,spaceAfter=7),
      'cell':ParagraphStyle('Cell',fontName='AACI',fontSize=8,leading=11.3,textColor=INK),
      'head':ParagraphStyle('TableHead',fontName='AACIBold',fontSize=8,leading=11,textColor=colors.white),
      'caption':ParagraphStyle('Caption',fontName='AACI',fontSize=7.4,leading=10.5,textColor=MUTED,spaceBefore=5,spaceAfter=9),
    })


def p(value,style='body',raw=False): return Paragraph(value if raw else esc(value),STYLES[style])


def table(headers, rows, widths):
    cells=[[p(x,'head') for x in headers]]
    for row in rows:
        cells.append([x if isinstance(x,Flowable) else p(x,'cell') for x in row])
    result=Table(cells,colWidths=widths,repeatRows=1,hAlign='LEFT')
    result.setStyle(TableStyle([
        ('BACKGROUND',(0,0),(-1,0),WINE),('VALIGN',(0,0),(-1,-1),'TOP'),
        ('LEFTPADDING',(0,0),(-1,-1),8),('RIGHTPADDING',(0,0),(-1,-1),8),
        ('TOPPADDING',(0,0),(-1,-1),8),('BOTTOMPADDING',(0,0),(-1,-1),8),
        ('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.white,CREAM]),
        ('LINEBELOW',(0,0),(-1,0),.5,WINE),('LINEBELOW',(0,1),(-1,-1),.35,LINE),
    ]))
    return result


def fitted_image(path,width,height):
    from PIL import Image as PILImage
    with PILImage.open(path) as im: w,h=im.size
    scale=min(width/w,height/h)
    return Image(str(path),width=w*scale,height=h*scale,hAlign='LEFT')


class Cover(Flowable):
    def __init__(self,data): super().__init__();self.data=data;self.width=499;self.height=700
    def draw(self):
        c=self.canv;c.saveState();c.setFillColor(CREAM);c.rect(-48,-100,600,900,fill=1,stroke=0)
        assets={a.get('asset_id'):a for a in self.data['arquivos']}
        logo=assets.get('IMG-0513')
        if logo:c.drawImage(str(DEST/logo['organizado']),0,636,width=175,height=53,preserveAspectRatio=True,mask='auto')
        c.setFillColor(WINE);c.setFont('AACIBold',9);c.drawString(0,605,'INVENTÁRIO E DOCUMENTAÇÃO DA CAPTURA LOCAL')
        c.setFont('AACISerif',36);c.drawString(0,546,'Mapa do acervo');c.setFont('AACISerif',48);c.drawString(0,491,'da AACI')
        text=p('Conteúdo extraído pelo HTTrack, organizado para consulta, reutilização e conferência. Captura e análise de 13 de novembro de 2026.')
        text.wrapOn(c,460,80);text.drawOn(c,0,436)
        c.setStrokeColor(LINE);c.line(0,414,499,414)
        for x,value,label in [(0,'949','arquivos lidos'),(128,'561','imagens'),(256,'26','documentos PDF'),(384,'4','vídeos locais')]:
            c.setFont('AACIBold',32);c.setFillColor(WINE);c.drawString(x,365,value)
            c.setFont('AACI',8.7);c.setFillColor(MUTED);c.drawString(x,344,label)
        text=p('45 fichas de páginas · 334 páginas de PDF · 12 vídeos externos referenciados','small');text.wrapOn(c,495,30);text.drawOn(c,0,307)
        for x,aid in [(0,'IMG-0486'),(170,'IMG-0258'),(340,'IMG-0425')]:
            a=assets.get(aid)
            if a and a.get('miniatura'):
                im=fitted_image(DEST/a['miniatura'],154,110);im.drawOn(c,x,170)
        c.setFillColor(INK);c.setFont('AACIBold',10);c.drawString(0,133,'Uma coleção local com rastreabilidade de origem.')
        text=p('Cada arquivo possui ID, caminho original, destino organizado e SHA-256. Referências sem cópia local e limitações da captura estão identificadas.','small');text.wrapOn(c,465,50);text.drawOn(c,0,91)
        c.setStrokeColor(LINE);c.line(0,65,499,65);c.setFillColor(MUTED);c.setFont('AACI',8)
        c.drawString(0,44,'Origem: mapeamento site/AACI');c.drawString(0,28,'Consulta: mapeamento site/AACI-organizado/index.html')
        c.restoreState()


class ReportDoc(BaseDocTemplate):
    def afterFlowable(self,flowable):
        if isinstance(flowable,Paragraph) and flowable.style.name=='Section':
            title=flowable.getPlainText();key='sec-'+base.slug(title)
            self.canv.bookmarkPage(key);self.canv.addOutlineEntry(title,key,0,False)
            self.notify('TOCEntry',(0,title,self.page,key))


def page_decoration(canvas,doc):
    if doc.page==1:return
    canvas.saveState();canvas.setStrokeColor(LINE);canvas.setLineWidth(.5);canvas.line(48,805,547,805)
    canvas.setFont('AACIBold',8);canvas.setFillColor(WINE);canvas.drawString(48,816,'AACI  |  MAPA DO ACERVO DIGITAL')
    canvas.setFont('AACI',7.5);canvas.setFillColor(MUTED);canvas.drawRightString(547,816,'CAPTURA 13/11/2026')
    canvas.line(48,39,547,39);canvas.drawString(48,25,'Inventário local · originais preservados · OCR identificado')
    canvas.drawRightString(547,25,f'{doc.page}')
    canvas.restoreState()


def public_summary_markdown(data):
    lines=['# Síntese do conteúdo público da AACI','', 'Fonte: captura local HTTrack de 13/11/2026. IDs são consultáveis no catálogo.','',
        '## Instituição e públicos','A AACI apresenta atuação desde janeiro de 2010, proteção social básica e fortalecimento de vínculos. O conteúdo descreve atendimento a crianças, adolescentes, mulheres, pessoas idosas e famílias (PAG-017, PAG-034, PAG-035).','',
        '## Serviços','SCFV; Casa de Atenção à Pessoa Idosa; fisioterapia gratuita; Apadrinhamento Afetivo; oficinas e inclusão digital; ações de segurança alimentar e cozinhas comunitárias (PAG-003, PAG-025, PAG-036 a PAG-040).','',
        '## Participação','Doações financeiras, Pix, transferência, campanhas, voluntariado e parcerias. Os canais e valores reproduzem o que consta no espelho, sem confirmação externa nesta análise (PAG-009 e PAG-035).','',
        '## Documentação','Os 26 PDFs locais totalizam 334 páginas. Há relatórios de atividades, portfólios, estatuto, ata, comprovante de viagem e prestações de contas. Seis outros documentos aparecem apenas como referências externas (PAG-033 e PAG-043).','',
        '## Endereços divergentes','A página inicial apresenta Rua Doutor Dias da Cruz, 487. Contato/Como Ajudar/Quem Somos mencionam Rua Guimarães Júnior, 90. Imagens do Apadrinhamento e SCFV indicam Rua General Almerindo da Silva Gomes, 133 e 162. As versões foram preservadas; não foi eleito um endereço único.','',
        '## Consulta por página']
    for page in data['paginas']:lines.extend([f"### {page['id']} | {page['titulo']}",PAGE_SUMMARY[page['id']],f"Origem: {page['url']}",''])
    target=DEST/'06_links_e_informacoes/resumo-do-conteudo-publico.md';target.parent.mkdir(parents=True,exist_ok=True);target.write_text('\n'.join(lines),encoding='utf-8')


def build_pdf(data):
    fonts();initialize_styles();OUTPUT.parent.mkdir(parents=True,exist_ok=True)
    stat=data['estatisticas'];assets=data['arquivos'];pages=data['paginas'];images=[a for a in assets if a['tipo']=='imagem'];docs=[a for a in assets if a['tipo']=='documento'];videos=[a for a in assets if a['tipo']=='video']
    width=A4[0]-96
    story=[Cover(data),PageBreak(),p('Guia de leitura','h1')]
    story.extend([p('O relatório resume o conteúdo e os limites do material recebido. O catálogo HTML permite visualizar os arquivos e os inventários CSV/JSON registram cada uma das 949 entradas.'),p('Os códigos PAG, IMG, VID, DOC e ARQ são chaves de consulta. No catálogo, procure pelo código para abrir o arquivo e verificar a sua fonte. Este PDF não contém o conteúdo integral de todos os documentos: ele descreve e referencia o acervo completo.'),Spacer(1,12)])
    toc=TableOfContents();toc.levelStyles=[ParagraphStyle('TOC',fontName='AACI',fontSize=10,leading=16,leftIndent=0,firstLineIndent=0,spaceBefore=9,textColor=INK)]
    story.extend([toc,PageBreak()])
    def section(title):story.extend([p(title,'h1')])
    def para(text):story.append(p(text))
    def sub(title):story.append(p(title,'h2'))
    def new():story.append(PageBreak())
    def source(ids):story.append(p('Fontes locais: '+ids+'. Os endereços completos constam no mapa de páginas e nos inventários.','small'))
    section('1. Resultado da extração')
    para(f'Foram lidos os {stat["arquivos_origem"]} arquivos da pasta recebida, totalizando {stat["bytes_origem"]/1000000:.2f} MB. A organização mantém {stat["arquivos_unicos"]} cópias únicas de conteúdo; {stat["duplicados_exatos"]} entradas idênticas por SHA-256 apontam para a mesma cópia organizada. Nenhum arquivo da captura original foi movido ou removido.')
    rows=[]
    for kind,label in [('pagina','HTML com estrutura de página'),('html-erro','HTML de erro HTTP'),('html-tecnico','HTML técnico/auxiliar'),('imagem','Imagens'),('documento','Documentos PDF'),('video','Vídeos MP4'),('javascript','JavaScript'),('css','CSS'),('fonte','Fontes tipográficas'),('httrack','Logs e cache HTTrack'),('auxiliar','Outros auxiliares')]:
        subset=[a for a in assets if a['tipo']==kind];rows.append([label,len(subset),f'{sum(a["bytes"] for a in subset)/1000000:.2f} MB'])
    story.append(table(['Categoria','Arquivos','Volume na origem'],rows,[width-170,65,105]))
    sub('O que está disponível para consulta')
    para('45 fichas de páginas; 561 arquivos de imagem distribuídos em 219 famílias; 26 PDFs com 334 páginas; 4 vídeos locais; 12 referências de vídeos externos; textos extraídos, contatos, formulários, links e documentos sem cópia local.')
    para('As 45 fichas incluem seis rotas de blog cujo corpo informa que o post não foi encontrado. Outras seis páginas têm texto escasso e conteúdo predominantemente visual ou de navegação. A contagem de fichas não significa 45 páginas completas e distintas de conteúdo editorial.')
    new();section('2. Método, leitura e rastreabilidade')
    for title,text in [('Leitura dos arquivos','Todos os arquivos físicos foram lidos integralmente para cálculo de SHA-256. O inventário registra tamanho, extensão, formato reconhecido, caminho original, caminho organizado e duplicatas.'),('Páginas e dados estruturados','Foram analisados os 107 HTMLs. O conteúdo principal das páginas foi separado de scripts e estilos; os dados estruturados Wix foram utilizados para recuperar títulos e referências de mídia.'),('Documentos PDF','As 334 páginas dos 26 PDFs passaram por extração de texto. Nas páginas com pouco ou nenhum texto selecionável, foi aplicado OCR Windows em português do Brasil: 111 páginas. Os textos mantêm identificação do método por página.'),('Imagens','Foram verificadas as 560 imagens raster e identificado o SVG adicional. Geraram-se miniaturas e folhas de contato das famílias. Aplicou-se OCR a 150 imagens representativas com resolução suficiente; marcas e contatos selecionados receberam rótulos após inspeção visual.'),('Vídeos','Os quatro MP4 passaram por decodificação integral para identificar erros. Foram registrados duração, dimensões e presença de áudio; quatro quadros por vídeo compõem a prévia. O áudio foi preservado, mas não foi transcrito.'),('Cache HTTrack','As 952 entradas do ZIP de cache foram lidas, com CRC verificado e hash registrado. O ZIP original também está preservado entre os arquivos técnicos.')]:
        sub(title);para(text)
    para('O OCR foi concluído em 261 itens, sem falhas de processamento. Isso indica conclusão técnica, não exatidão de cada palavra: grafias, números e trechos de baixa qualidade precisam ser conferidos nos originais.')
    source('08_catalogos/inventario-completo.csv; entradas-cache.csv; acervo.json')
    new();section('3. Conteúdo relevante ao público')
    sub('Instituição, história e propósito')
    para('A AACI se apresenta como organização sem fins lucrativos em funcionamento desde janeiro de 2010, voltada à proteção social e ao fortalecimento dos vínculos familiares e comunitários. O material reúne missão, visão, valores, equipe, instalações, parceiros e participação nos Objetivos de Desenvolvimento Sustentável. Há referências ao Criança Esperança em 2018 e ao incentivo da Becton Dickinson em 2021.')
    source('PAG-017, PAG-019 a PAG-021, PAG-034 e PAG-035')
    sub('Serviços e projetos')
    story.append(table(['Frente','O que a captura descreve'],[
      ['SCFV','Atividades gratuitas de convivência, desenvolvimento, arte, cultura, recreação, apoio social e psicológico. A página apresenta crianças de 4 a 14 anos, adolescentes de 14 a 17, mulheres a partir de 18 e pessoas idosas acima de 60 como públicos dos grupos.'],
      ['Casa de Atenção à Pessoa Idosa','Atendimento diurno, alimentação, oficinas, convivência e acompanhamento de serviço social, psicologia e fisioterapia; apoio às famílias e à autonomia.'],
      ['Fisioterapia','Atendimento gratuito à comunidade. A reportagem de julho de 2024 cita 54 atendimentos naquele contexto; esse número não foi tratado como capacidade atual.'],
      ['Apadrinhamento Afetivo','Apresentação do programa, papel dos padrinhos, acolhida, avaliações, capacitação, perguntas frequentes e resultados de 2022. As orientações foram preservadas como conteúdo da versão capturada.'],
      ['Segurança alimentar','Campanhas, doações e registro de cozinhas comunitárias, incluindo notícia de atuação em Muriaé.'],
      ['Acolhimento e parcerias','Termos, demonstrativos e registros da Casa de Passagem, acolhimento emergencial, apadrinhamento, cuidados à pessoa idosa e SCFV.'],
    ],[115,width-115]))
    source('PAG-003 a PAG-006, PAG-025, PAG-031, PAG-033 e PAG-036 a PAG-040')
    new();sub('Rotinas, horários e atividades')
    para('Os horários abaixo são os declarados na página espelhada, sem atualização de agenda nesta análise.')
    story.append(table(['Grupo','Horários capturados'],[['Crianças - manhã','Segunda a sexta: chegada às 08:00; acolhida e lanche; atividades; almoço às 10:30; saída às 11:00.'],['Crianças - tarde','Segunda a sexta: chegada às 13:00; acolhida e lanche; atividades; jantar às 16:30; saída às 17:00.'],['Mulheres','Terça-feira, das 13:00 às 15:00.'],['Pessoas idosas','Quinta-feira, das 14:00 às 16:00.'],['Adolescentes','Sexta-feira, das 14:00 às 16:00.']],[125,width-125]))
    para('As atividades descritas incluem Oficina Master Chef, reciclagem e arte, cinema interativo, roda de conversa, datas comemorativas, aniversariantes, reuniões de família, capoeira, teatro, informática, inglês e Muay Thai. Também são apresentados psicologia e serviço social. A grafia dos projetos e os textos originais permanecem nas fichas.')
    source('PAG-037 e PAG-038')
    sub('Como participar e acompanhar')
    para('A captura reúne doações financeiras e de itens, voluntariado, parcerias, notícias, galerias, newsletter, recrutamento e orientações aos colaboradores sobre acesso a holerites. Não foram identificados holerites individuais baixados. Seis estruturas de formulário foram mapeadas, incluindo contato, newsletter, candidatura e solicitações sobre dados; seus serviços de envio não funcionam como backend local.')
    para('Na versão recebida, a página Como Ajudar publica Pix pelo CNPJ 11550709000187 e dados Bradesco, agência 2868-1, conta 0010212-1. Esses dados foram documentados como parte da captura, com sua origem, sem validação externa de vigência.')
    source('PAG-008 a PAG-010, PAG-013, PAG-035, PAG-041 e PAG-042')
    new();sub('Contatos e versões divergentes')
    story.append(table(['Informação capturada','Onde aparece'],[
      ['Rua Doutor Dias da Cruz, 487, Nova Era, Juiz de Fora','Rodapé da página inicial (PAG-017).'],
      ['Rua Guimarães Júnior, 90, Nova Era, Juiz de Fora','Contato, Como Ajudar, Quem Somos, privacidade e documentos.'],
      ['Rua General Almerindo da Silva Gomes, 133','Imagem de contato do Apadrinhamento (IMG-0392); também consta no título SEO da página inicial.'],
      ['Rua General Almerindo da Silva Gomes, 162','Imagem de contato do SCFV (IMG-0538).'],
      ['(32) 98476-7527','Social no rodapé da página inicial.'],
      ['(32) 3226-4832 e (32) 98855-9201','Contato/Como Ajudar e imagem do SCFV.'],
      ['(32) 3211-5475 e (32) 98889-0665','Leitura visual da imagem de contato do Apadrinhamento (IMG-0392).'],
      ['aaci-@hotmail.com; aacisocial@hotmail.com; projetosaaci@hotmail.com; apadrinhamento@aaci.org.br','Páginas de contato, participação e imagem do Apadrinhamento.'],
    ],[290,width-290]))
    para('As fontes divergem entre si. A organização preservou todas as versões e não escolheu um endereço ou telefone como o único atual. Os contatos obtidos de imagens têm o método de leitura identificado no CSV.')
    sub('Privacidade e atendimento')
    para('A política publicada trata de finalidades, dados pessoais, compartilhamento, armazenamento, cookies, segurança e direitos dos titulares. A página de Telemarketing reúne perguntas frequentes e um formulário de solicitação. Este relatório cataloga o conteúdo; não avalia a atualidade jurídica das orientações publicadas.')
    source('PAG-009, PAG-010, PAG-017, PAG-022, PAG-039 e PAG-041; IMG-0392 e IMG-0538')
    new();section('4. Mapa das 45 fichas de páginas')
    para('Cada ficha possui texto principal, referência de origem, imagens associadas e links. O inventário inclui páginas visuais e as rotas de post sem conteúdo recuperado para tornar explícita a cobertura da captura.')
    rows=[]
    for page in pages:
        link=f'<b>{esc(page["titulo"])}</b><br/><font color="#6c6269">{esc(page["tema"])}</font><br/><link href="{esc(page["url"])}" color="#64152e">Fonte de origem</link>'
        rows.append([page['id'],p(link,'cell',True),PAGE_SUMMARY[page['id']]])
    story.append(table(['ID','Página / origem','Conteúdo mapeado'],rows,[54,175,width-229]))
    new();section('5. Imagens: identidade, pessoas e atividades')
    para('Os 561 arquivos de imagem incluem fotografias, logos, ícones, artes educativas, materiais de privacidade, organograma, QR codes, banners e miniaturas de vídeo. Há 219 famílias de mídia: os diferentes recortes e resoluções são mantidos como variantes; duplicatas exatas compartilham a cópia de mesmo hash.')
    groups=Counter(a.get('grupo','') for a in images)
    story.append(table(['Grupo de consulta','Arquivos de imagem'],[[k,v] for k,v in sorted(groups.items())],[width-100,100]))
    para('Os formatos reconhecidos são 327 JPEG, 231 PNG, 2 GIF e 1 SVG. As miniaturas não substituem os arquivos: o catálogo informa as dimensões e permite abrir a cópia organizada. Em 69 famílias, o melhor arquivo disponível tem dimensão máxima inferior a 180 px; esse conjunto inclui ícones legítimos e prévias de carregamento do Wix.')
    para('As folhas de contato mostram fotografias de instalações, convivência, campanhas e entregas de Natal, além de marcas de parceiros, atividades e materiais institucionais. A classificação temática usa a página de origem; alguns rótulos foram complementados após inspeção visual. Ela não é uma identificação automática das pessoas retratadas.')
    source('03_imagens; 08_catalogos/imagens.csv; 09_previsualizacoes/folhas-de-contato')
    sub('Amostra visual do acervo')
    by_asset={a.get('asset_id'):a for a in assets}
    samples=[]
    for aid in ['IMG-0486','IMG-0513','IMG-0425','IMG-0258','IMG-0078','IMG-0402','IMG-0407','IMG-0476','IMG-0054']:
        a=by_asset[aid]
        sample=[fitted_image(DEST/a['miniatura'],148,100),p(aid+' · '+(a.get('rotulo_editorial') or a.get('grupo','')),'caption')]
        samples.append(sample)
    grid=Table([samples[i:i+3] for i in range(0,len(samples),3)],colWidths=[width/3]*3)
    grid.setStyle(TableStyle([('VALIGN',(0,0),(-1,-1),'TOP'),('TOPPADDING',(0,0),(-1,-1),8),('BOTTOMPADDING',(0,0),(-1,-1),8)]));story.append(grid)
    new();section('6. Vídeos locais e referências externas')
    para('Os quatro MP4 locais totalizam 57,63 MB e passaram pela decodificação integral sem erros reportados. Todos têm áudio. As durações abaixo foram medidas nos arquivos; os resumos decorrem do contexto da página e da inspeção dos quadros, sem transcrição do áudio.')
    for video in videos:
        content=[p(video['asset_id']+' | '+video['titulo'],'h2'),p(f"{video['duracao']} · {video.get('largura')} × {video.get('altura')} px · {video['bytes']/1000000:.2f} MB",'small'),p(VIDEO_SUMMARY[video['asset_id']])]
        image=fitted_image(DEST/video['miniatura'],85,118)
        row=Table([[image,content]],colWidths=[120,width-120]);row.setStyle(TableStyle([('VALIGN',(0,0),(-1,-1),'TOP'),('TOPPADDING',(0,0),(-1,-1),8),('BOTTOMPADDING',(0,0),(-1,-1),12)]));story.append(row)
    new();sub('Catálogo externo: referências, não downloads')
    rows=[]
    for video in data['videos_externos']:
        tech=video.get('url_tecnica_capturada',video['url']);provider='YouTube' if 'youtube.com' in tech else 'Wix / streaming'
        label=p(f'{esc(video["titulo"])}<br/><link href="{esc(video["url"])}" color="#64152e">Abrir referência pública</link>','cell',True)
        rows.append([label,video.get('duracao_legivel',video['duracao_declarada']),provider])
    story.append(table(['Título','Duração declarada','Origem'],rows,[width-160,65,95]))
    para('Sete referências são do YouTube e cinco de streaming Wix. Os endereços técnicos assinados do streaming são temporários; os links de consulta apontam para a página pública de vídeos. Não foram confundidos com os quatro MP4 efetivamente baixados.')
    new();section('7. Biblioteca dos 26 documentos PDF')
    para('Os documentos locais somam 334 páginas. Cada um tem cópia integral, prévia da primeira página, URL de origem e texto por página. Quando houve OCR, o arquivo de texto registra esse método. Os resumos abaixo descrevem a natureza do conteúdo, sem reproduzir dados pessoais de signatários ou conferir valores contábeis.')
    rows=[]
    for document in docs:
        title=p(f'<b>{esc(document["titulo"])}</b><br/>{esc(DOC_SUMMARY[document["asset_id"]])}','cell',True)
        tech=f'{document["numero_paginas"]} páginas\n{document["bytes"]/1000000:.2f} MB\n{document.get("paginas_ocr",0)} com OCR'
        rows.append([document['asset_id'],title,tech])
    story.append(table(['ID','Documento e conteúdo','Leitura'],rows,[53,width-146,93]))
    source('PAG-033 e PAG-043; 05_documentos; 02_textos/documentos; 08_catalogos/documentos.csv')
    sub('Documentos referenciados sem arquivo local')
    missing=[link for link in data['links'] if '.pdf' in link['url'] and not link['presente_localmente']]
    for link in missing:
        para(link['rotulo']+' - referência encontrada em '+link['pagina']+', hospedada em domínio externo filesusr.com. O PDF não faz parte da captura local.')
    para('A sequência de relatórios locais não é uma série anual contínua: foram baixados SCFV 2015 a 2021 e SCFV 2025, além dos relatórios de 2022 do Apadrinhamento e de 2023 da Casa de Atenção à Pessoa Idosa. Os SCFV 2022, 2023 e 2024 constam entre as referências sem cópia local.')
    new();section('8. Organização e acesso aos arquivos')
    para('A pasta AACI mantém o espelho original. AACI-organizado é a coleção de consulta, com cópias únicas, nomes legíveis e correspondência completa para os caminhos recebidos. Os arquivos HTML originais foram guardados como fonte técnica; para navegar pelo espelho use a pasta original, pois o HTTrack depende dos seus caminhos relativos.')
    story.append(table(['Pasta / arquivo','Como utilizar'],[
      ['index.html','Ponto de entrada; abre diretamente no navegador, sem instalação.'],
      ['01_paginas','45 fichas de leitura com texto, imagens e links.'],
      ['02_textos','Textos das páginas, das 334 páginas PDF e OCR de imagens.'],
      ['03_imagens','Imagens agrupadas por tema, preservando suas variantes.'],
      ['04_videos','Os quatro MP4 locais e CSV dos vídeos externos.'],
      ['05_documentos','PDFs separados em governança, relatórios, portfólios, campanhas e prestação de contas.'],
      ['06_links_e_informacoes','Contatos, formulários, links públicos, referências sem arquivo local e síntese editorial.'],
      ['07_tecnico','Fontes HTML, scripts, estilos, fontes tipográficas, cache, logs e auxiliares.'],
      ['08_catalogos','Inventários CSV, mapa de páginas, duplicatas, transferências e JSON completo.'],
      ['09_previsualizacoes','Miniaturas, primeiras páginas dos PDFs, quadros dos vídeos e folhas de contato.'],
    ],[145,width-145]))
    sub('Pesquisar e localizar a origem')
    para('Abra index.html e escolha imagens, documentos, vídeos ou páginas. A busca aceita nome, ID e conteúdo textual disponível. Em imagens, a opção de variantes amplia a lista para os diferentes arquivos da mesma família. Para auditoria, use o inventário completo: o campo organizado mostra a cópia e origem aponta para o espelho recebido; SHA-256 identifica o conteúdo.')
    new();section('9. Limites da captura e próximas conferências')
    para('O log registra execução de 11:32:06 a 11:53:17 de 13/11/2026 e finalização do espelho, mas informa três links com falha de transferência. Também registra 67 erros, 29 avisos e seis mensagens; contagens de tentativas no log não equivalem a arquivos ausentes.')
    story.append(table(['Achado','Efeito para consulta e reutilização'],[
      ['Três imagens f000.jpg sem transferência completa','Prévia de vídeos referenciada no log, mas sem arquivo correspondente completo. Os MP4 locais foram verificados separadamente.'],
      ['Seis documentos externos sem cópia','Somente o rótulo e a referência foram preservados. Não são apresentados como documentos extraídos.'],
      ['50 HTMLs de erro e 12 HTMLs técnicos','Mantidos no inventário e na pasta técnica, sem misturar com conteúdo editorial.'],
      ['Seis rotas de blog com post não encontrado','As fichas registram a mensagem recebida; nenhum texto do post foi inventado.'],
      ['69 famílias abaixo de 180 px','Parte são ícones; parte são prévias de carregamento. Confira resolução antes de reutilizar como foto ou banner.'],
      ['Endereços e telefones divergentes','As versões e fontes são preservadas. A instituição precisa confirmar quais canais devem ser publicados como atuais.'],
      ['Dados estruturados e serviços externos','Players, inscrições, newsletter, formulários e integrações podem depender de conexão e de serviços da plataforma original.'],
      ['Conteúdo histórico e OCR','Datas, números e orientações pertencem às fontes capturadas. OCR é texto auxiliar e pode conter erros.'],
    ],[185,width-185]))
    sub('Conferências prioritárias para uma futura atualização do site')
    para('Confirmar contatos por unidade; obter os seis documentos ausentes; substituir prévias de baixa resolução por originais autorizados; conferir o estado dos links de notícias e dos players; e revisar as integrações de formulários antes de oferecê-las como serviço ativo. Este trabalho não alterou o site HTML/CSS/JS existente no repositório.')
    new();section('10. Índice das famílias de imagem')
    para('Uma entrada representativa por família visual. O inventário de imagens contém todas as variantes e caminhos. As dimensões indicam o melhor arquivo disponível no espelho, não uma resolução recuperada da internet.')
    rows=[]
    representatives=sorted([a for a in images if a.get('melhor_da_familia')],key=lambda a:(a.get('grupo',''),a['asset_id']))
    for a in representatives:
        label=a.get('rotulo_editorial') or (a['rotulos'][0] if a['rotulos'] else a.get('grupo','Sem rótulo'))
        rows.append([a['asset_id'],label[:110],f'{a.get("largura","?")} × {a.get("altura","?")}',a.get('grupo','')])
    story.append(table(['ID','Rótulo / contexto','Pixels','Grupo'],rows,[58,215,76,width-349]))
    para('A organização integral é documentada em inventario-completo.csv. As 949 linhas de arquivos originais não são repetidas aqui para manter este PDF como síntese consultável; os anexos digitais fornecem os detalhes completos.')
    doc=ReportDoc(str(OUTPUT),pagesize=A4,leftMargin=48,rightMargin=48,topMargin=54,bottomMargin=49,title='Mapa do acervo digital da AACI',author='Documentação local da captura HTTrack',subject='Inventário, organização e resumo do conteúdo extraído em 13/11/2026',allowSplitting=True)
    frame=Frame(48,49,width,A4[1]-103,id='body',leftPadding=0,rightPadding=0,topPadding=0,bottomPadding=0)
    doc.addPageTemplates(PageTemplate(id='report',frames=frame,onPage=page_decoration))
    doc.multiBuild(story)
    shutil.copy2(OUTPUT,DEST/OUTPUT.name)
    return OUTPUT


def write_readme(data):
    stat=data['estatisticas']
    text=f'''# Acervo AACI organizado

Abra **index.html** para consultar o catálogo local. Não precisa instalar nada ou executar os scripts. Para reprodução, o navegador deve suportar MP4. Links externos exigem internet.

## O que foi organizado

- {stat['arquivos_origem']} arquivos originais, lidos integralmente para inventário e SHA-256.
- {stat['arquivos_unicos']} cópias únicas; {stat['duplicados_exatos']} duplicatas exatas apontam para a mesma cópia.
- 45 fichas HTML, incluindo seis rotas de post sem conteúdo recuperado.
- 561 imagens em 219 famílias, com variantes e miniaturas.
- 26 PDFs, com 334 páginas. OCR identificado em 111 páginas.
- OCR de 150 imagens representativas.
- 4 vídeos MP4 locais, validados por decodificação, e 12 referências de vídeos externos.

A origem **../AACI** foi preservada. Esta coleção é uma reorganização por cópias e não altera os caminhos necessários ao HTTrack. HTMLs originais ficam em 07_tecnico/html-fontes; para navegar pelo site espelhado, use a pasta original. Os arquivos de consulta em 01_paginas são fichas limpas, não réplicas funcionais do Wix.

## Onde encontrar

| Local | Conteúdo |
|---|---|
| index.html | Entrada do catálogo |
| imagens.html | Busca por ID, rótulo, contexto e OCR; opção de variantes |
| documentos.html | Os 26 PDFs e textos |
| videos.html | MP4 locais e referências externas |
| paginas.html | As 45 fichas de página |
| 01_paginas | Fichas limpas de consulta |
| 02_textos | Texto HTML, texto PDF por página e OCR de imagens |
| 03_imagens | Imagens por tema |
| 04_videos | Arquivos locais e catálogo externo |
| 05_documentos | Governança, relatórios, portfólios, campanhas e contas |
| 06_links_e_informacoes | Contatos, formulários, links, ausências e resumo editorial |
| 07_tecnico | HTML-fonte, scripts, estilos, fontes, logs e cache |
| 08_catalogos | CSV, JSON, transferências, cache e duplicatas |
| 09_previsualizacoes | Miniaturas, quadros e folhas de contato |
| Relatorio-do-acervo-AACI.pdf | Relatório resumido com fontes, cobertura e limitações |

## Proveniência e limites

Captura e análise: **13/11/2026**. Os dados descrevem o conteúdo recebido, sem atualização ou validação externa de vigência. Os nomes e grupos usam rótulos do site, páginas de origem e inspeção visual selecionada; os IDs permitem rastrear todos os nomes.

O log do HTTrack informa três transferências incompletas. Há seis documentos externos citados mas não baixados, prévias de baixa resolução, páginas de erro e rotas de blog sem texto. Vídeos externos são referências, não arquivos baixados. Alguns links Wix assinados expiram; por isso o catálogo oferece a página pública como referência estável.

OCR é aproximação pesquisável, sujeito a erros de palavras e números. Os arquivos originais devem ser consultados para conferência. O áudio dos vídeos foi preservado sem transcrição. Os formulários foram mapeados, mas não possuem backend local. Não foram enviadas mensagens ou inscrições.

Os contatos variam entre páginas e imagens. As versões foram preservadas em contatos-extraidos.csv, sem escolher um endereço único atual. Os arquivos técnicos incluem o cache e a configuração da captura; não integram o resumo público.

## Identificadores

- **ARQ**: uma linha para cada arquivo original.
- **PAG**: ficha de página capturada.
- **IMG**: arquivo de imagem, com família e variantes.
- **VID**: vídeo local.
- **DOC**: documento PDF.
- **SHA-256**: comparação exata do conteúdo. Duplicatas compartilham a cópia organizada e continuam separadas no inventário.

Os scripts de reprodução do processo estão em ../../tools. Os resultados de conferência são registrados em 08_catalogos/verificacao-final.json. O site HTML/CSS/JS da raiz do repositório não foi alterado por esta organização.
'''
    (DEST/'00_LEIA-ME.md').write_text(text,encoding='utf-8')


def main():
    data=json.loads((DEST/'08_catalogos/acervo.json').read_text(encoding='utf-8'))
    for page in data['paginas']: page['resumo_editorial']=PAGE_SUMMARY[page['id']]
    for rec in data['arquivos']:
        if rec.get('asset_id') in DOC_SUMMARY:rec['resumo_editorial']=DOC_SUMMARY[rec['asset_id']]
        if rec.get('asset_id') in VIDEO_SUMMARY:rec['resumo_editorial']=VIDEO_SUMMARY[rec['asset_id']]
    base.dump(DEST/'08_catalogos/acervo.json',data)
    public_summary_markdown(data);write_readme(data)
    result=build_pdf(data)
    print('PDF:',result)
    print('Cópia na coleção:',DEST/result.name)


if __name__=='__main__':main()
