# Sistema de Transcrição e Geração Automática de Vídeos Didáticos

Este projeto utiliza as APIs Whisper e GPT-4o da OpenAI para:
1. Transcrever áudios educacionais com timestamps precisos
2. Segmentar o conteúdo em blocos conceituais usando IA
3. Gerar slides de apresentação automaticamente
4. Enriquecer e refinar o conteúdo dos slides com IA
5. Criar apresentações PowerPoint profissionais prontas para uso
6. **✨ NOVO:** Gerar vídeos didáticos completos com legendas sincronizadas

## 📋 Funcionalidades

### Fase I - Transcrição
- Transcrição automática de arquivos de áudio (MP3, WAV, M4A, etc.)
- Timestamps precisos para cada palavra (início e fim em segundos)
- Exportação dos resultados em formato JSON estruturado

### Fase II - Geração de Slides
- Segmentação semântica inteligente usando GPT-4o
- Identificação automática de blocos conceituais (introdução, conceitos, despedida)
- Geração automática de slides com título e bullets concisos
- Exportação de slides em formato JSON estruturado

### Fase III - Enriquecimento de Conteúdo ✨ NOVO
- Refinamento automático de títulos e bullets usando GPT-4o
- Eliminação inteligente de redundâncias
- Criação de frases introdutórias para listas
- Melhoria de clareza e profissionalismo do conteúdo
- Mantém fidelidade ao texto original

### Fase IV - Validação e Sincronização
- Validação automática de fidelidade do conteúdo ao texto original
- Correção automática de slides com erros de conteúdo
- Sincronização determinística de timestamps com matching fuzzy

### Fase V - Geração de PowerPoint
- Criação automática de apresentações PowerPoint (.pptx)
- Suporte a frases introdutórias e estruturas hierárquicas
- Suporte a templates customizados com design de marca
- Formatação profissional de títulos e bullets
- Geração pronta para apresentação

### Fase VI - Geração de Vídeo ✨ NOVO
- Conversão automática de slides em imagens PNG de alta resolução
- Geração de script de apresentação sincronizado com timestamps
- Criação de legendas automáticas a partir da transcrição Whisper
- Renderização de vídeo MP4 com moviepy
- Sincronização perfeita entre slides, áudio e legendas
- Qualidade Full HD (1920x1080) pronta para publicação

## 🚀 Instalação

### 1. Clonar/baixar o projeto

```bash
cd video-slides
```

### 2. Instalar dependências

```bash
pip install -r requirements.txt
```

### 3. Configurar API Key

1. Copie o arquivo `.env.example` para `.env`:
   ```bash
   copy .env.example .env
   ```

2. Edite o arquivo `.env` e adicione sua chave da OpenAI:
   ```
   OPENAI_API_KEY=sk-seu-token-aqui
   ```

## 📁 Estrutura do Projeto

```
video-slides/
├── audios/              # Pasta para arquivos de áudio (input)
├── output/              # Pasta para arquivos JSON gerados
├── src/                 # Código fonte modular
│   ├── __init__.py      # Inicialização do pacote
│   ├── config.py        # Configuração e variáveis de ambiente
│   ├── audio_utils.py   # Manipulação de arquivos de áudio
│   ├── transcription.py # Transcrição com API Whisper
│   ├── output.py        # Salvamento de transcrições
│   ├── prompts.py       # Prompts de IA (chunking + slides + enriquecimento)
│   ├── chunking.py      # Segmentação semântica com GPT
│   ├── slide_generator.py # Geração de slides com GPT
│   ├── slide_enricher.py # Enriquecimento de conteúdo dos slides
│   ├── validation.py    # Validação de conteúdo
│   ├── timestamp_matcher.py # Sincronização de timestamps
│   └── pptx_generator.py # Geração de PowerPoint
├── main.py              # Orquestrador principal
├── criar_template.py    # Script auxiliar para criar template
├── requirements.txt     # Dependências Python
├── template.pptx        # Template PowerPoint (opcional)
├── .env.example         # Exemplo de configuração
├── .env                 # Sua configuração (não comitar!)
└── README.md            # Este arquivo
```

### Arquitetura Modular

O projeto foi estruturado em módulos independentes:

**Fase I - Transcrição:**
- **src/config.py**: Gerencia configurações e API keys
- **src/audio_utils.py**: Localização e validação de arquivos de áudio
- **src/transcription.py**: Comunicação com API Whisper
- **src/output.py**: Salvamento de transcrições em JSON

**Fase II - Geração de Slides:**
- **src/prompts.py**: Prompts estruturados para IA (chunking + geração + enriquecimento)
- **src/chunking.py**: Segmentação semântica usando GPT-4o
- **src/slide_generator.py**: Geração de slides a partir de chunks

**Fase III - Enriquecimento:**
- **src/slide_enricher.py**: Refinamento e enriquecimento de conteúdo dos slides

**Fase IV - Validação e Sincronização:**
- **src/validation.py**: Validação e correção de conteúdo dos slides
- **src/timestamp_matcher.py**: Sincronização determinística de timestamps

**Fase V - Geração de PowerPoint:**
- **src/pptx_generator.py**: Criação de apresentações PowerPoint com suporte a frases introdutórias

**Fase VI - Geração de Vídeo:** ✨ NOVO
- **src/pptx_to_images.py**: Conversão de slides PowerPoint em imagens PNG
- **src/show_script_generator.py**: Geração de script de apresentação com timestamps
- **src/subtitle_generator.py**: Criação de legendas sincronizadas (SRT e moviepy)
- **src/video_renderer.py**: Renderização de vídeo final com moviepy

**Orquestração:**
- **main.py**: Coordena o fluxo de transcrição e geração de slides
- **montar_video.py**: ✨ NOVO - Orquestra a geração completa de vídeo
- **criar_template.py**: Utilitário para criar templates customizados

## 💻 Como Usar

### 1. Adicionar áudio

Coloque seu arquivo de áudio (`.mp3`, `.wav`, etc.) na pasta `audios/`:

```
audios/
└── meu_audio.mp3
```

### 2. Executar o script

```bash
python main.py
```

O script executará automaticamente **todo o fluxo**:

**Fase I - Transcrição:**
- Detecta o primeiro arquivo de áudio na pasta `audios/`
- Envia para a API Whisper
- Processa timestamps palavra por palavra
- Salva transcrição em `output/meu_audio.json`

**Fase II - Geração de Slides:**
- Analisa a estrutura do conteúdo com GPT-4o
- Identifica blocos conceituais (introdução, conceitos, despedida)
- Gera slides automaticamente para cada conceito

**Fase III - Enriquecimento de Conteúdo:**
- Refina títulos e bullets com GPT-4o
- Elimina redundâncias automaticamente
- Cria frases introdutórias quando apropriado
- Melhora clareza e profissionalismo

**Fase IV - Validação e Sincronização:**
- Valida fidelidade do conteúdo ao texto original
- Corrige automaticamente slides com erros
- Sincroniza timestamps precisos usando matching determinístico
- Salva slides em `output/meu_audio_slides.json`

**Fase V - Geração de PowerPoint:**
- Cria apresentação PowerPoint automaticamente
- Formata frases introdutórias e bullets
- Salva em `output/meu_audio.pptx`
- Pronta para apresentação!

### 3. ✨ NOVO: Gerar vídeo didático

Para gerar um vídeo completo a partir dos slides:

```bash
python montar_video.py
```

**O sistema automaticamente:**
- Converte slides PowerPoint em imagens PNG
- Gera script de apresentação sincronizado
- Cria legendas automáticas da transcrição
- Renderiza vídeo MP4 com áudio e legendas
- Salva em `output/meu_audio.mp4`

**Pronto para YouTube, Vimeo ou qualquer plataforma!** 🎬

Para mais detalhes, veja [README_VIDEO.md](README_VIDEO.md)

### 4. (Opcional) Customizar template

Se desejar usar um template customizado com design de marca:

```bash
python criar_template.py
```

Isso criará um arquivo `template.pptx` que você pode customizar no PowerPoint com:
- Cores da marca
- Logotipos
- Fontes personalizadas
- Layouts específicos

O sistema usará automaticamente este template se ele existir.

### 4. Verificar resultados

Você terá **3 arquivos** na pasta `output/`:

#### 4.1 Transcrição (`meu_audio.json`):

```json
{
  "arquivo_audio": "meu_audio.mp3",
  "total_palavras": 150,
  "palavras": [
    {
      "palavra": "Olá",
      "inicio": 0.5,
      "fim": 0.8
    },
    {
      "palavra": "mundo",
      "inicio": 0.9,
      "fim": 1.2
    }
  ]
}
```

#### 4.2 Slides (`meu_audio_slides.json`):

```json
{
  "arquivo_original": "meu_audio.json",
  "total_slides": 5,
  "slides": [
    {
      "timestamp_inicio": 15.4,
      "tipo": "conceito",
      "titulo_conceito": "Fotossíntese",
      "slide_title": "Fotossíntese: Processo de Produção de Energia",
      "slide_bullets": [
        "Processo realizado por plantas e algas",
        "Converte luz solar em energia química",
        "Produz glicose e libera oxigênio",
        "Ocorre nos cloroplastos das células vegetais"
      ]
    }
  ]
}
```

#### 4.3 Apresentação PowerPoint (`meu_audio.pptx`):

Arquivo PowerPoint completo pronto para apresentação com:
- Slides formatados profissionalmente
- Títulos e bullets organizados
- Design customizado (se usar template)
- Compatível com Microsoft PowerPoint, Google Slides, LibreOffice

Basta abrir o arquivo e apresentar! 🎉

## 📝 Exemplo de Saída no Console

```
======================================================================
SISTEMA DE TRANSCRIÇÃO E GERAÇÃO DE SLIDES
======================================================================

[FASE I] Transcrição do áudio
----------------------------------------------------------------------
Arquivo selecionado: roteiro_1.mp3
Enviando arquivo para a API da OpenAI...
Transcrição recebida.

======================================================================
TRANSCRIÇÃO COM TIMESTAMPS
======================================================================

Palavra: 'Olá', Início: 0.50s, Fim: 0.80s
Palavra: 'estudante', Início: 0.90s, Fim: 1.20s
...

Transcrição salva em: output\roteiro_1.json

✓ Processo concluído com sucesso!
✓ Total de palavras transcritas: 450

======================================================================
[FASE II] Geração de Slides
----------------------------------------------------------------------

Analisando estrutura do conteúdo com IA...
✓ Identificados 6 blocos conceituais

Gerando slides a partir dos chunks...
  Processando chunk 1/6: introducao (ignorado)
  Processando chunk 2/6: conceito ✓
  Processando chunk 3/6: conceito ✓
  Processando chunk 4/6: conceito ✓
  Processando chunk 5/6: conceito ✓
  Processando chunk 6/6: despedida (ignorado)

✓ 4 slides gerados

✓ Slides salvos em: output\roteiro_1_slides.json

======================================================================
PREVIEW DOS SLIDES GERADOS
======================================================================

[Slide 1] - Timestamp: 8.20s
Título: Fotossíntese: Processo de Produção de Energia
Bullets:
  • Processo realizado por plantas e algas
  • Converte luz solar em energia química
  • Produz glicose e libera oxigênio
  • Ocorre nos cloroplastos das células vegetais

======================================================================

======================================================================
[FASE III] Validacao, Correcao de Conteudo e Sincronizacao de Timestamps
----------------------------------------------------------------------

[VALIDAÇÃO DE CONTEÚDO] Verificando fidelidade ao texto original...
OK Conteudo de todos os slides esta correto!

[SINCRONIZACAO DETERMINISTICA] Matching preciso de timestamps...
  OK Slide 0: 8.20s (OK)
  OK Slide 1: 15.40s (OK)
  OK Slide 2: 22.60s (OK)
  OK Slide 3: 30.10s (OK)

OK Sincronizacao concluida:
  - 4/4 slides sincronizados
  - 0 timestamps corrigidos

======================================================================
[FASE IV] Geração de PowerPoint
----------------------------------------------------------------------
Carregados 4 slides do JSON
Criando apresentação com template padrão
Gerando 4 slides...
  Slide 1/4: conceito - Fotossíntese: Processo de Produção de Energia... (8.20s)
  Slide 2/4: conceito - Respiração Celular: Liberação de Energia... (15.40s)
  Slide 3/4: conceito - Ciclo do Carbono: Equilíbrio Natural... (22.60s)
  Slide 4/4: conceito - Cadeia Alimentar: Fluxo de Energia... (30.10s)

OK Apresentação PowerPoint salva em: output\roteiro_1.pptx
OK Total de slides criados: 4

======================================================================
OK PROCESSO CONCLUIDO COM SUCESSO!
======================================================================
OK Palavras transcritas: 450
OK Chunks identificados: 6
OK Slides gerados: 4
OK Validacao de conteudo: OK
OK Sincronizacao de timestamps: 4/4 slides
OK Correcoes de timestamp: 0 ajustes realizados
OK Apresentacao PowerPoint: roteiro_1.pptx
======================================================================
```

## 🔧 Formatos de Áudio Suportados

- MP3
- WAV
- M4A
- MP4
- MPEG
- MPGA
- WEBM

## ⚠️ Observações

- Certifique-se de que o arquivo `.env` não seja commitado no Git
- **Custos de API**: O processo usa Whisper + GPT-4o (2 chamadas por conceito)
- A API Whisper tem limite de 25MB por arquivo
- O processamento completo pode levar alguns minutos dependendo do tamanho
- O script processa automaticamente o primeiro arquivo da pasta `audios/`
- Áudios educacionais funcionam melhor (estrutura: introdução → conceitos → despedida)

## 🎯 Casos de Uso

- **Professores**: Transformar aulas gravadas em slides automaticamente
- **Criadores de conteúdo**: Gerar apresentações a partir de roteiros narrados
- **Estudantes**: Criar resumos estruturados de videoaulas
- **Equipes de treinamento**: Converter webinars em material didático

## 🛠️ Tecnologias Utilizadas

- Python 3.7+
- OpenAI API (Whisper + GPT-4o)
- python-dotenv
- python-pptx (geração de PowerPoint)

## 🧠 Como Funciona a IA

### Segmentação Semântica
O GPT-4o analisa a transcrição completa e identifica automaticamente:
- Introdução do conteúdo
- Blocos conceituais (cada conceito = definição + exemplos)
- Despedida

### Geração de Slides
Para cada conceito identificado, o GPT-4o:
1. Extrai o tema principal para o título (máx. 10 palavras)
2. Identifica 3-5 pontos-chave para bullets (máx. 15 palavras cada)
3. Reformula com clareza e concisão
4. Mantém fidelidade ao conteúdo original

### Enriquecimento de Conteúdo ✨
O GPT-4o refina os slides gerados através de:
1. **Refinamento de títulos**: Torna títulos mais descritivos e informativos
2. **Melhoria da redação**: Reescreve bullets para maior clareza e profissionalismo
3. **Eliminação de redundâncias**: Detecta padrões repetitivos e reestrutura
4. **Frases introdutórias**: Cria contexto para listas de itens relacionados

**Exemplo de transformação:**

Antes:
```
Título: Exemplos de Textos Instrucionais
• Os conectivos como antes
• Os conectivos como depois
• Os conectivos como assim que
```

Depois:
```
Título: Identificando Textos Instrucionais: Conectivos Temporais
Frase introdutória: Para identificar textos instrucionais, procure por conectivos temporais como:
• Antes
• Depois
• Assim que
```

## 📄 Licença

Este projeto é de código aberto para fins educacionais.
