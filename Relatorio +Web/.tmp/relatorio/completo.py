from pathlib import Path
setup=Path('.tmp/relatorio/organizado.py').read_text(encoding='utf-8-sig')
exec(setup[:setup.index("exec(compile(source,")])

source=source.replace("p('2 Etapas e atividades realizadas','H1A')", "p('O levantamento reuniu demandas de comunicação institucional e de acesso às formas de apoio. A proposta buscou reduzir informações redundantes, valorizar serviços destinados a crianças e idosos e apresentar caminhos claros para quem deseja conhecer, contatar ou contribuir com a AACI. O protótipo permitiu discutir essas decisões antes da consolidação das páginas.')\np('2 Etapas e atividades realizadas','H1A')")
source=source.replace('O relatório geral registra a realização da visita e o envio posterior da fotografia pela instituição.', 'A aproximação presencial ajudou a contextualizar as necessidades do website, e a instituição compartilhou posteriormente o registro fotográfico do encontro.')
source=source.replace('Fonte: visita 1.jpeg; contexto registrado no relatório geral.', 'Encontro realizado em 21/05/2026.')
source=source.replace('Fonte: visita 2.jpeg.', 'Apresentação do protótipo em outubro de 2026.')
source=source.replace("p('4 Site antes e depois','H1A')", "p('4 Site antes e depois no computador','H1A')")
source=source.replace('Segundo o relatório geral, a implementação local reunia', 'A implementação local reuniu')
source=source.replace('A mesma fonte registra verificações estruturais, de interação e de layout em diferentes larguras de tela. Esses registros documentam o estágio técnico, sem representar auditoria integral de acessibilidade, teste financeiro ou operação definitiva.', 'O desenvolvimento incluiu verificações estruturais, de interação e de layout em diferentes larguras de tela. A adaptação da interface contemplou a reorganização dos elementos para telas menores, com navegação compacta e maior destaque às ações de contato e doação. Essas verificações não equivalem a uma auditoria integral de acessibilidade ou a testes de transações financeiras.')
source=source.replace("p('Situação da entrega','H2A')", "p('Organização do conteúdo e experiência de uso','H2A')\np('O mapeamento das páginas existentes apoiou a seleção de textos, links e imagens para a nova estrutura. Serviços sociais, notícias, depoimentos e documentos de transparência foram organizados para facilitar a consulta. O trabalho também envolveu a revisão das formas de contribuição, associando chamadas de doação aos canais de apoio da instituição.')\np('A versão para celulares passou a apresentar o conteúdo em sequência vertical, com menu recolhido e ações principais visíveis. No computador, a distribuição mais ampla permite destacar simultaneamente a apresentação institucional e as opções de contribuição. Essa diferenciação entre telas procura manter a identidade do site e adequar a leitura ao espaço disponível.')\np('Situação da entrega','H2A')")
source=source.replace('A continuidade deve priorizar a conclusão dos ajustes, a validação institucional e o acompanhamento do uso do website.', 'As reuniões e visitas aproximaram a equipe da realidade institucional e orientaram decisões sobre conteúdo e interface. A continuidade deve priorizar a conclusão dos ajustes, a validação institucional e o acompanhamento do uso do website.')
mobile='''page();p('5 Adaptação para celulares','H1A')
p('A comparação no celular evidencia a reorganização da página para uma tela estreita. Na versão anterior, a captura apresenta trechos do menu cortados nas laterais e uma imagem ampliada que ocupa grande parte da área visível. Na versão reformulada, o cabeçalho, a mensagem principal e as ações de apoio se distribuem dentro da largura da tela.')
assets['mobile_antes']=Path('C:/Users/RBENIS~1/AppData/Local/Temp/codex-clipboard-6bdb9238-835a-4db4-8352-58a3c4c9775f.png')
assets['mobile_depois']=Path('C:/Users/RBENIS~1/AppData/Local/Temp/codex-clipboard-e8b07424-91c3-4ca2-98bb-d30d278e4e2f.png')
for key in ['mobile_antes','mobile_depois']:
 dest=TMP/(key+'.png');dest.write_bytes(assets[key].read_bytes());assets[key]=dest
mobile_images=[]
for key in ['mobile_antes','mobile_depois']:
 im=PILImage.open(assets[key]);mobile_images.append(Image(str(assets[key]),width=165,height=165*im.height/im.width))
comparison=Table([[Paragraph('<b>Antes</b>',styles['CenterA']),Paragraph('<b>Depois</b>',styles['CenterA'])],mobile_images],colWidths=[235,235])
comparison.setStyle(TableStyle([('ALIGN',(0,0),(-1,-1),'CENTER'),('VALIGN',(0,0),(-1,-1),'TOP'),('BOTTOMPADDING',(0,0),(-1,0),8)]))
story.append(comparison);story.append(Spacer(1,10))
t=doc.add_table(rows=2,cols=2);t.autofit=False
for j,(label,key) in enumerate([('Antes','mobile_antes'),('Depois','mobile_depois')]):
 t.columns[j].width=Pt(235)
 pa=t.cell(0,j).paragraphs[0];pa.alignment=WD_ALIGN_PARAGRAPH.CENTER;pa.add_run(label).bold=True
 pa=t.cell(1,j).paragraphs[0];pa.alignment=WD_ALIGN_PARAGRAPH.CENTER;pa.add_run().add_picture(str(assets[key]),width=Pt(165))
p('Figura 5 — Comparação da página inicial no celular: versão anterior à esquerda e reformulada à direita.','CaptionA')
p('Melhorias visíveis','H2A')
p('O menu horizontal foi substituído por um botão de navegação compacto. A mensagem principal aparece em um bloco com texto ajustado à largura disponível, e os cartões de contribuição seguem a disposição vertical da página. Na parte inferior, a interface apresenta uma barra com “Fale com a AACI” e “Quero doar”, além do botão flutuante do WhatsApp.')
p('As capturas demonstram a adaptação visual nesse tamanho de tela. O funcionamento dos menus, dos links e dos fluxos de doação deve acompanhar a validação final em diferentes dispositivos e navegadores.')

'''
source=source.replace("page();p('5 Resultados e considerações finais','H1A')", mobile+"page();p('6 Resultados e considerações finais','H1A')")
source=source.replace('Relatorio_Tecnico_+Web_Organizado','Relatorio_Tecnico_+Web_Atualizado')
exec(compile(source,'completo','exec'))
