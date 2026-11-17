from pathlib import Path
base=Path('.tmp/relatorio/build.py').read_text(encoding='utf-8-sig')
exec(base.split("pic('logo',300)")[0])
styles['CenterA'].spaceAfter=3
styles['CenterA'].leading=15
styles['TitleA'].fontSize=23
styles['TitleA'].leading=28
doc.styles['Title'].font.size=Pt(23)
pic('logo',240)
space(15)
p('Relatório Técnico do Projeto +Web','TitleA')
p('Desenvolvimento do website institucional da AACI','CenterA')
p('Projeto de extensão • UniAcademia Centro Universitário','CenterA')
space(15)
p('Equipe','CenterA')
names=['Rúben Israel Esterci de Souza','Naamã Lima ferreira','Angelo Bessa','Vitor Hugo Almeida Carmo','Carlos Eduardo de Paiva Paula','Gustavo Henrique Do Nascimento Gonçalves','Gabriel Alves Valverde','Davi Rossini de Paula Pereira','Vinicius Fontes Nocera','Cláudio Bispo de Almeida Filho','Arthur Esteves Gomes','Rhuan de Souza Leite','Lucas Ribeiro Figueiredo Souza','Angelo Giacomini']
for n in names:
 pa=p(n,'CenterA');pa.paragraph_format.space_after=Pt(3);pa.paragraph_format.line_spacing=1
space(23)
p('Juiz de Fora — MG','CenterA')
p('16 de novembro de 2026','CenterA')

page();p('1 Objetivo e metodologia','H1A')
p('O +Web, projeto de extensão do UniAcademia, desenvolveu uma proposta de reformulação do website da Associação de Apoio a Crianças e Idosos (AACI). O objetivo foi reorganizar as informações institucionais, destacar os serviços sociais e facilitar o acesso às formas de doação e contato. A demanda partiu da necessidade de reduzir a dispersão de conteúdos e melhorar a navegação do site existente. [1–2]')
p('A metodologia combinou levantamento de requisitos, visitas técnicas, prototipação, mapeamento de conteúdo e implementação, com avaliação da AACI ao longo do processo. O primeiro semestre concentrou planejamento e documentação; o segundo, desenvolvimento e adequação da proposta. [1–3]')
p('2 Etapas e atividades realizadas','H1A')
table(['Etapa','Atividades'],[
 ('Planejamento e requisitos','Formação da equipe e aproximação com a AACI. Na reunião remota de 04/05/2026, foram priorizadas doações, navegação, atualização de conteúdo e atendimento.'),
 ('Visita e organização','Visita em 21/05/2026 para conhecer a instituição. Registro das decisões, organização das frentes de trabalho e definição da identidade do +Web.'),
 ('Prototipação','Elaboração da proposta visual em setembro e envio à AACI em 01/10. Apresentação presencial em 21/10, com avaliação favorável e orientações sobre conteúdos.'),
 ('Desenvolvimento','Mapeamento de páginas, textos, links e imagens em novembro. Organização de serviços, notícias, transparência, doações e contato em uma versão navegável.'),
 ('Revisão institucional','Retorno favorável da AACI em 13/11, com solicitação de troca de duas fotos e retirada de contatos de apadrinhamento afetivo.')
],[115,355])
p('A segunda reunião reforçou a apresentação das atividades com idosos, dos documentos de transparência e dos materiais audiovisuais. A instituição ficou responsável pela seleção de informações e mídias, e a equipe acadêmica pela organização e implementação. O chatbot foi previsto como possibilidade para 2027, mediante alinhamento acadêmico. [2–3]')

page();p('3 Visitas técnicas e registros','H1A')
p('Primeira visita','H2A')
p('O encontro de 21/05/2026 complementou o levantamento remoto e aproximou o grupo da rotina da AACI. O relatório geral registra a realização da visita e o envio posterior da fotografia pela instituição. [3]')
pic('visita1',285,'Figura 1 — Primeira visita à AACI. Fonte: visita 1.jpeg; contexto registrado no relatório geral.')
p('Segunda visita','H2A')
p('Em 21/10/2026, Rúben, Arthur e Rhuan apresentaram o protótipo na sede da AACI. Foram discutidos layout, serviços, transparência e conteúdos necessários ao desenvolvimento. [2]')
pic('visita2',300,'Figura 2 — Registro fornecido da segunda visita à AACI. Fonte: visita 2.jpeg.')

page();p('4 Site antes e depois','H1A')
p('As capturas mostram a reorganização visual da página inicial. A versão reformulada representa o estágio apresentado do projeto, ainda sujeito aos ajustes e ao aceite institucional. [3]')
p('Antes','H2A')
pic('antes',445,'Figura 3 — Site anterior: menu distribuído em várias linhas e apresentação institucional no bloco inicial. Fonte: captura fornecida.')
p('Depois','H2A')
pic('depois',445,'Figura 4 — Versão reformulada: navegação agrupada, destaque às doações e seção de serviços. Fonte: captura fornecida.')
p('Principais mudanças: menu mais concentrado; botão “Quero doar” em destaque; cartão com contribuição sugerida; maior hierarquia visual; acesso à transparência e botão flutuante do WhatsApp. Os valores e exemplos de apoio exibidos não comprovam doações ou benefícios realizados.','CaptionA')

page();p('5 Resultados e considerações finais','H1A')
p('O projeto produziu levantamento de necessidades, registros de reuniões e visitas, protótipo visual, mapeamento de conteúdos e uma versão navegável do website. A comparação evidencia a reorganização da navegação e maior destaque às formas de apoio, em resposta às prioridades apresentadas pela AACI. [1–3]')
p('Segundo o relatório geral, a implementação local reunia 20 páginas HTML, recursos de doação por Pix com QR Code, encaminhamento de contato pelo WhatsApp e biblioteca com 26 PDFs. A mesma fonte registra verificações estruturais, de interação e de layout em diferentes larguras de tela. Esses registros documentam o estágio técnico, sem representar auditoria integral de acessibilidade, teste financeiro ou operação definitiva. [3, seção 8]')
p('Situação da entrega','H2A')
p('Até 16/11/2026, o retorno institucional era favorável, mas permaneciam ajustes de imagens e contatos, consolidação da segunda ata e formalização do aceite e da entrega técnica. A migração para o domínio da AACI e a entrega de acessos administrativos não estavam comprovadas. O chatbot e os cadastros mais complexos permaneceram como possibilidades de continuidade. [2–3]')
p('Conclusão','H2A')
p('O +Web aplicou conhecimentos de tecnologia e comunicação a uma demanda real da AACI, avançando do diagnóstico para uma solução navegável. A continuidade deve priorizar a conclusão dos ajustes, a validação institucional e o acompanhamento do uso do website. Aumento de acessos, doações ou impacto social depende de medição posterior. [3]')
p('Fontes e comprovações','H2A')
p('[1] ATA DE REUNIÃO 01 (Aaci). Reunião remota de 04/05/2026, às 16h45. Levantamento de requisitos e definição das fases.','CaptionA')
p('[2] ATA DE REUNIÃO 02 (Aaci). Reunião presencial de 21/10/2026, às 9h15. Apresentação do protótipo e encaminhamentos.','CaptionA')
p('[3] Relatorio Geral.pdf. Versão documental de 16/11/2026. Cronologia, atividades, situação técnica e pendências do projeto.','CaptionA')
p('Registros visuais: visita 1.jpeg; visita 2.jpeg; capturas fornecidas das versões anterior e reformulada do site; logotipo do UniAcademia fornecido para a capa.','CaptionA')

def footer_pdf(canvas,document):
 if document.page>1:
  canvas.setFont('Arial',8);canvas.setFillColor(colors.HexColor('#555555'))
  canvas.drawRightString(533,32,f'+Web  |  Relatório técnico  |  {document.page}')
doc.save(OUT/'Relatorio_Tecnico_+Web_Reduzido.docx')
SimpleDocTemplate(str(OUT/'Relatorio_Tecnico_+Web_Reduzido.pdf'),pagesize=(595.276,841.89),leftMargin=62.36,rightMargin=62.36,topMargin=56.69,bottomMargin=56.69,title='Relatório Técnico do Projeto +Web',author='Equipe +Web | UniAcademia').build(story,onFirstPage=footer_pdf,onLaterPages=footer_pdf)
print('Versão reduzida criada')
