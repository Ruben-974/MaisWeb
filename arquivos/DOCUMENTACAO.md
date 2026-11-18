# AACI — site institucional

Site estático em HTML, CSS e JavaScript, com Bootstrap 5.3.8 local. Mantém a paleta vinho/coral/creme, os títulos em serifa e os cartões do modelo `Homepage AACI - Desktop.pdf`.

## Como abrir

Abra o **index.html** com Live Server no VS Code. Ou execute, a partir da raiz do projeto:

```powershell
python -m http.server 5500 --bind 127.0.0.1 --directory .
```

Acesse `http://127.0.0.1:5500`. Não há instalação ou build obrigatório. Use HTTP/Live Server para os players incorporados: em `file://`, os botões encaminham ao YouTube para evitar falhas de referência do player.

## Organização

São 21 páginas: início; quem somos; serviços; convivência; pessoa idosa; apadrinhamento; fisioterapia; como ajudar; transparência; notícias; cinco artigos em `pages/noticias/`; galeria; vídeos; AACI na mídia; contato; privacidade; e trabalhe conosco.

Os quantitativos da página inicial ficam em `arquivos/dados/home-statistics.json`, com fonte, período e distinção entre pessoas, inscrições e vagas. A seção aparece antes da história institucional. A página `pages/aaci-na-midia.html` reúne quatro reportagens com os players e as miniaturas já disponíveis. O WhatsApp fixo utiliza o canal de doações e informações `(32) 98855-9201` e não envia mensagens automaticamente.

A página inicial apresenta os serviços e conduz aos detalhes. Biblioteca, perguntas dos programas, textos completos e notícias têm seus próprios espaços.

## Funcionalidades

- Menu responsivo, modal de doação, valores validados e cópia de Pix.
- QR Pix e botão “Copiar Pix com valor” atualizados conforme a quantia digitada ou selecionada. O QR original da AACI foi decodificado e conferido com o CNPJ `11550709000187`; seus dados são preservados, com inclusão do valor e recálculo do CRC16. Valores inválidos ocultam o QR e desabilitam sua cópia.
- Contato validado que prepara a mensagem para revisão e envio pelo visitante no WhatsApp. Os dados não são guardados em armazenamento local e não há confirmação fictícia de envio.
- Sete vídeos do YouTube carregados após clique e distribuídos por assunto, com links alternativos.
- Quatro vídeos MP4 com fonte externa e cópia local de segurança, com controles nativos.

As fontes externas de imagens, documentos e MP4 são priorizadas conforme `arquivos/dados/external-media.json`. A conferência encontrou 87 endereços disponíveis. As imagens e os MP4 têm retorno automático ao arquivo local; os 26 PDFs oferecem a fonte externa e o download da cópia local. A imagem principal do modelo e o favicon permanecem locais. O comportamento está em `assets/js/media.js`; a galeria também conserva a alternativa local ao ampliar as fotos. Os recortes das três fotos editadas são mantidos pelas transformações da CDN Wix.

A verificação `node arquivos/tools/test_aaci_external_media.cjs` testou o carregamento externo com os arquivos locais bloqueados, a reprodução de um MP4 externo e o retorno aos arquivos locais com a rede externa bloqueada. O relatório está em `arquivos/output/site-external-media-tests.json`.
- Cinco notícias com texto, data original e mídia correspondente.
- Galeria com 18 imagens, pesquisa, categorias, ampliação, teclado e retorno de foco.
- Biblioteca com 26 PDFs locais, pesquisa, categoria, ano, abertura e download.
- Perguntas frequentes e cópia de links das notícias.

## Arquivos

`styles.css` preserva a base do modelo. `site-pages.css` organiza as páginas internas e adaptações responsivas. `script.js` mantém os controles de doação; `assets/js/site.js` contém filtros, players, galeria, contato e compartilhamento.

Fotos, logos e posters ficam em `assets/img`; vídeos, em `assets/media`; PDFs, em `assets/documents`. Os manifestos `arquivos/dados/asset-map.json` e `arquivos/dados/document-map.json` registram origem e identificação. Os PDFs e MP4 foram copiados com SHA-256 idêntico ao acervo. Os documentos são carregados somente quando o visitante os abre ou baixa.

O espelho HTTrack e o catálogo `arquivos/mapeamento AACI/AACI-organizado` permanecem como referências independentes. O site principal não precisa dessas pastas para navegar, reproduzir os arquivos locais ou consultar os PDFs.

## Conteúdo e canais

Fonte: captura de 13/11/2026. Quatro notícias são de 2026; a reportagem de fisioterapia é de 04/07/2024. Seus números históricos não foram transformados em indicadores atuais. Fotos distintas representam os serviços e atividades; o banner mantém a imagem do modelo. As marcas são apresentadas como organizações presentes na trajetória, sem presumir parceria vigente.

Os sete IDs YouTube responderam HTTP 200 no oEmbed e no endpoint de incorporação; isso não comprova reprodução completa em navegador. Cinco vídeos Wix cujos endpoints diretos responderam 403 foram retirados da listagem, que antes encaminhava para o portal anterior. Os vídeos com fonte direta e os sete players YouTube foram preservados. Seis PDFs referenciados e ausentes da captura permanecem como links externos.

Os contatos variam entre páginas da captura. O atendimento institucional usa o endereço da página inicial (Rua Doutor Dias da Cruz, 487), com orientação para confirmar a visita. Telefones e e-mails dos programas são apresentados separadamente. As doações usam os canais publicados em Como Ajudar.

A página Trabalhe conosco encaminha ao contato com a equipe para informações sobre oportunidades e orientações de candidatura. Doações, mensagens e solicitações utilizam os canais da AACI por WhatsApp e e-mail. As páginas e os textos apresentam este site como o portal da instituição, com navegação interna para doações, privacidade e contato. O compartilhamento de notícias utiliza o endereço da própria página aberta.

O QR com valor é gerado localmente no navegador, sem transmitir os dados a geradores externos. O payload original e as fontes estão em `arquivos/dados/pix-config.json`; a implementação segue o [Manual de Padrões para Iniciação do Pix do Banco Central](https://www.bcb.gov.br/content/estabilidadefinanceira/pix/Regulamento_Pix/II_ManualdePadroesparaIniciacaodoPix.pdf), com campo 54 e CRC16/CCITT-FALSE. A geração visual usa `qrcode-generator` 2.0.4, distribuído localmente em `assets/js/vendor/qrcode.js`, sob licença MIT em `assets/licenses/qrcode.LICENSE`. É um QR Pix estático com valor preenchido, atualizado pelo site; não há integração bancária para confirmação automática de pagamento.

Os cartões do banner e a seção de contribuição mostram exemplos concretos: R$ 25 para um kit de desenho, R$ 50 para materiais escolares, R$ 100 para uma cesta básica compacta e R$ 200 para duas cestas compactas. O seletor atualiza o exemplo, o destaque e o valor levado ao modal de doação.

As estimativas estão em `arquivos/dados/donation-impact.json`, com preços, fontes e consulta em 13/11/2026. Foram arredondadas a partir de referências de varejo: [kit de desenho de R$ 24,90](https://www.universodaart.com.br/produtos/kit-escolar-12-lapis-de-cor-2-lapis-preto-borracha-apontador-bic/), [kit com caderno de R$ 45,90](https://www.rarapapelaria.com.br/produtos/kit-escolar-caderno-e-lapis-de-cor-metalizado-qvw4w/) e [cesta econômica de R$ 99,90](https://www.lojapoupemaisrs.com.br/produtos/cesta-basica-economico/). Não incluem frete, não constituem uma média estatística e não representam custos confirmados pela AACI. A cesta compacta é um exemplo de conjunto de alimentos, sem promessa de suprir um mês de alimentação. O aviso público informa a variação dos preços e a aplicação das doações conforme as necessidades da instituição.

## Regenerar as páginas

Edite `arquivos/tools/build_aaci_site.py` ou os componentes de `arquivos/tools/site-templates/` e execute:

```powershell
python -X utf8 arquivos/tools/build_aaci_site.py
```

O comando utiliza os manifestos e `arquivos/tools/site-research.json`, sem modificar o espelho ou o catálogo. Os HTMLs gerados já estão prontos para uso.

## Validação

A sintaxe, as referências locais, âncoras, IDs e as interações das 21 páginas são verificadas por ferramentas locais e testes de DOM com Bootstrap. Navegação, quantitativos, história compacta, atalhos fixos, doação e reportagens também foram conferidos em Chrome headless nas larguras de 320, 375, 768, 950, 1200 e 1440 px, com revisão das capturas em celular e desktop. Não houve teste em aparelhos físicos. Os resultados e as capturas estão em `arquivos/output/site-layout-tests.json` e nas imagens de `arquivos/output/`.

Para repetir a verificação de layout, inicie um servidor local na porta 8765 com `--directory .`, disponibilize `playwright-core` no `NODE_PATH` e execute `node arquivos/tools/test_aaci_layout.cjs`. É possível definir `AACI_PREVIEW_URL` e `AACI_BROWSER_PATH` para outro endereço ou executável de navegador.

O Pix tem verificações próprias: `node arquivos/tools/test_aaci_pix.cjs` confere o payload e seus limites; `node arquivos/tools/test_aaci_pix_browser.cjs` testa os controles e captura os QRs reais em 320, 375 e 1440 px; `python -X utf8 arquivos/tools/validate_aaci_pix.py` decodifica as nove capturas com OpenCV e confere valor, dados oficiais, CRC16 independente e igualdade com o código copiado. Os relatórios estão em `arquivos/output/site-pix-browser-tests.json` e `arquivos/output/site-pix-validation.json`. Essa validação não realizou transferência bancária.
