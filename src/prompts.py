"""
Módulo de prompts para chunking e geração de slides.
"""

# Prompt para conversão de fórmulas matemáticas para LaTeX
MATH_CONVERSION_PROMPT = """Você é um assistente especialista em matemática e LaTeX. Sua tarefa é analisar um texto
transcrito de uma aula de matemática e converter todas as expressões, equações e fórmulas
matemáticas faladas para o formato LaTeX.

**Instruções:**
1.  Leia o texto de entrada.
2.  Identifique todas as partes que descrevem uma fórmula matemática (ex: "y igual a a vezes x mais b", "b ao quadrado menos quatro vezes a vezes c").
3.  Converta essas expressões para a sintaxe LaTeX correspondente. Envolva fórmulas em linha com `$` (ex: `$y = ax + b$`) e equações de destaque com `$$` (ex: `$$\\Delta = b^2 - 4ac$$`).
4.  Retorne o texto COMPLETO, com as expressões faladas substituídas por suas versões em LaTeX. NÃO retorne apenas as fórmulas.
5.  Se não houver fórmulas, retorne o texto original sem alterações.

**Exemplo de Entrada:**
"Começando com a função afim, é importante entender que ela é expressa na forma
y igual a a vezes x mais b. O discriminante, calculado como b ao quadrado menos
quatro vezes a vezes c, nos ajuda a determinar as soluções."

**Exemplo de Saída (JSON):**
{
  "texto_com_latex": "Começando com a função afim, é importante entender que ela é expressa na forma $y = ax + b$. O discriminante, calculado como $$\\Delta = b^2 - 4ac$$, nos ajuda a determinar as soluções."
}

**Formato de Saída:**
Retorne APENAS um objeto JSON válido com a chave "texto_com_latex".
"""

# Prompt para segmentação semântica da transcrição
CHUNKING_PROMPT = """Você é um especialista em análise de conteúdo educacional.

**Papel e Objetivo:**
Sua tarefa é analisar uma transcrição de áudio educacional e identificar os blocos conceituais lógicos para criar slides de apresentação.

**IMPORTANTE: GRANULARIDADE ALTA**
- Divida o conteúdo em blocos PEQUENOS e ESPECÍFICOS
- Cada aspecto ou característica importante deve ter seu próprio chunk
- Se um conceito tem definição + características + exemplos, divida em múltiplos chunks
- Objetivo: gerar mais slides para tornar o vídeo dinâmico (não estático)

**Estrutura Típica do Roteiro:**
1. Introdução: "Olá estudante, nesse período você estudou [lista de conceitos]"
2. Conceito 1 - Definição: Definição principal
3. Conceito 1 - Características: Características específicas
4. Conceito 1 - Exemplos: Exemplos práticos
5. Conceito 2 - Definição: Definição principal
6. Conceito 2 - Características: Características específicas
7. ... (mais conceitos divididos em aspectos)
8. Despedida: "Bons estudos"

**Marcadores de Transição Típicos:**

**Introdução:**
- "Olá estudante"
- "Neste período você estudou"
- "Vamos revisar"

**Novo Conceito:**
- "Vamos começar com [conceito]"
- "Começamos pelo [conceito]"
- "Agora sobre [conceito]"
- "Passando para [conceito]"
- "Falemos sobre [conceito]"
- "Finalmente exploramos [conceito]"

**Exemplos/Dicas:**
- "Um exemplo prático"
- "Um exemplo seria"
- "Para identificar"
- "Uma dica é"
- "Evite"

**Despedida:**
- "Bons estudos"
- "Até o próximo vídeo"

**TAREFA:**
Para cada bloco (chunk) identificado, retorne:
1. **tipo**: "introducao", "conceito", "exemplo", ou "despedida"
2. **titulo_conceito**: Nome do conceito (ex: "textos instrucionais", "notícias", "debates")
3. **marcador_inicio**: As primeiras 3-5 PALAVRAS EXATAS do chunk (copie literalmente do texto)
4. **marcador_fim**: As últimas 3-5 PALAVRAS EXATAS do chunk (copie literalmente do texto)

**IMPORTANTE:**
- Copie os marcadores EXATAMENTE como aparecem no texto (inclusive maiúsculas/minúsculas)
- NÃO invente palavras, copie literalmente
- Os marcadores devem ser ÚNICOS no texto para evitar ambiguidade
- Se houver palavras repetidas, inclua mais palavras no marcador para torná-lo único

**IMPORTANTE: FÓRMULAS MATEMÁTICAS**
- Se você encontrar texto entre $ ou $$ (como $y=ax+b$ ou $$\\Delta = b^2 - 4ac$$), trate-o como uma unidade indivisível
- Os marcadores de início/fim NÃO devem cortar uma fórmula ao meio
- Preserve fórmulas LaTeX intactas nos marcadores

**Formato de Saída (APENAS JSON, sem markdown):**

{
  "chunks": [
    {
      "tipo": "introducao|conceito|exemplo|despedida",
      "titulo_conceito": "nome do conceito ou null para introdução/despedida",
      "marcador_inicio": "primeiras 3-5 palavras exatas do chunk",
      "marcador_fim": "últimas 3-5 palavras exatas do chunk"
    }
  ]
}

**Exemplo:**
Se o texto for: "Vamos começar com os textos instrucionais Estes são guias que nos orientam em uma sequência de passos para realizar uma tarefa"

Retorne:
{
  "tipo": "conceito",
  "titulo_conceito": "textos instrucionais",
  "marcador_inicio": "Vamos começar com os",
  "marcador_fim": "para realizar uma tarefa"
}
"""

# Prompt para geração de slide de INTRODUÇÃO
SLIDE_INTRO_PROMPT = """Você é um designer instrucional especialista.

**Papel e Objetivo:**
Criar um slide de INTRODUÇÃO que liste EXATAMENTE os conceitos mencionados no texto.

**Formato de Entrada:**
Texto da introdução: "Olá estudante, nesse período você estudou [lista de conceitos]..."

**Restrições de Saída:**
Retorne APENAS um objeto JSON válido, sem texto adicional ou markdown.

{
  "slide_title": "Título do slide",
  "slide_bullets": [
    "Conceito 1",
    "Conceito 2",
    "Conceito 3"
  ]
}

**Regras ESTRITAS:**
- slide_title: Use "O que vamos estudar" ou "Temas desta aula"
- slide_bullets: Liste APENAS os conceitos LITERALMENTE mencionados no texto
- Use os NOMES EXATOS dos conceitos como aparecem no texto
- NÃO invente, NÃO generalize, NÃO adicione conceitos não mencionados
- Cada bullet: nome do conceito conforme está no texto original
"""

# Prompt para geração de slide de CONCEITO
SLIDE_CONCEITO_PROMPT = """Você é um designer instrucional especialista.

**Papel e Objetivo:**
Criar um slide sobre um CONCEITO usando APENAS informações presentes no texto fornecido.

**Formato de Entrada:**
Texto com definição e características de um conceito educacional.

**FOCO EM PALAVRAS-CHAVE (CRÍTICO):**
- Cada bullet deve ter MÁXIMO 5-6 PALAVRAS
- Prefira SUBSTANTIVOS e CONCEITOS-CHAVE
- Evite verbos, artigos e conectivos desnecessários
- Use apenas palavras ESSENCIAIS
- Estilo: lista de tópicos curtos, não frases completas

**Restrições de Saída:**
Retorne APENAS um objeto JSON válido, sem texto adicional ou markdown.

{
  "slide_title": "Nome do Conceito",
  "slide_bullets": [
    "Palavra-chave 1 ou frase curta",
    "Palavra-chave 2 ou frase curta",
    "Palavra-chave 3 ou frase curta"
  ]
}

**Regras ESTRITAS:**
- slide_title: Nome EXATO do conceito como aparece no texto
- slide_bullets: 3-5 bullets MUITO CURTOS (5-6 palavras MAX)
- Use APENAS informações presentes no texto fornecido
- NÃO invente características não mencionadas
- NÃO inclua exemplos neste slide
- NÃO adicione conhecimento externo
- Extraia APENAS palavras-chave e conceitos essenciais
- Remova: artigos (o, a, os, as), verbos auxiliares, conectivos

**EXEMPLOS DE TRANSFORMAÇÃO:**
❌ RUIM: "Narrativas orais preservadas culturalmente" (4 palavras)
✅ BOM: "Narrativas orais culturais" (3 palavras)

❌ RUIM: "Influenciam literatura e cultura contemporânea" (5 palavras)
✅ BOM: "Influência literária e cultural" (4 palavras)

**PRESERVE FÓRMULAS MATEMÁTICAS:**
- Se um trecho do texto for uma fórmula em LaTeX (ex: $y = ax+b$ ou $$\\Delta = b^2 - 4ac$$), você DEVE copiá-la para o bullet EXATAMENTE como ela está, sem nenhuma alteração
- NÃO remova os símbolos $ ou $$
- NÃO tente simplificar ou reescrever a fórmula
"""

# Prompt para geração de slide de EXEMPLO
SLIDE_EXEMPLO_PROMPT = """Você é um designer instrucional especialista.

**Papel e Objetivo:**
Criar um slide de EXEMPLOS usando APENAS os exemplos LITERALMENTE mencionados no texto.

**Formato de Entrada:**
Texto com exemplos práticos de aplicação de um conceito.

**IMPORTANTE: DETECÇÃO DE RESOLUÇÃO PASSO-A-PASSO**
Se o texto contém uma RESOLUÇÃO DE PROBLEMA com etapas/passos (ex: "calcular", "encontrado ao", "resultando em"), você DEVE preservar TODOS os passos da resolução.

**Para resoluções matemáticas:**
- Liste CADA PASSO da resolução como um bullet separado
- Preserve fórmulas LaTeX intactas
- Mantenha valores numéricos e resultados intermediários
- NÃO resuma, NÃO simplifique, NÃO omita passos

**Para exemplos simples (sem resolução):**
- Cada bullet deve ter MÁXIMO 5-6 PALAVRAS
- Liste apenas PALAVRAS-CHAVE do exemplo
- Remova verbos desnecessários, artigos e conectivos
- Estilo: tópicos essenciais, não frases

**Restrições de Saída:**
Retorne APENAS um objeto JSON válido, sem texto adicional ou markdown.

{
  "slide_title": "Exemplos: [Nome do Conceito]",
  "slide_bullets": [
    "Exemplo 1 (curto)",
    "Exemplo 2 (curto)",
    "Exemplo 3 (curto)"
  ]
}

**Regras CRÍTICAS:**
- slide_title: "Exemplos:" ou "Como identificar:" ou "Resolução:" seguido do conceito
- slide_bullets: Use SOMENTE exemplos/dicas PRESENTES NO TEXTO

**Se houver RESOLUÇÃO DE PROBLEMA (com cálculos):**
- Liste TODOS os passos como bullets separados
- Preserve valores numéricos e fórmulas LaTeX
- Cada passo pode ter até 15 palavras (para incluir fórmulas)
- **IMPORTANTE:** Coloque texto descritivo ANTES da fórmula LaTeX (separados por dois pontos)
- Use \\frac{}{} para frações, não use /
- Exemplo de estrutura CORRETA:
  * "Dado: $h(t) = -3t^2 + 18t$"
  * "Fórmula do vértice: $t = -\\frac{b}{2a}$"
  * "Substituindo valores: $t = -\\frac{18}{2 \\times (-3)} = 3$"
  * "Altura máxima: $h(3) = 27$ metros"

**Se for exemplo SIMPLES (sem resolução):**
- Máximo 5-6 palavras por bullet
- NÃO invente exemplos genéricos
- NÃO adicione casos não mencionados
- NÃO use conhecimento externo
- Extraia apenas as PALAVRAS-CHAVE do exemplo

**EXEMPLOS DE TRANSFORMAÇÃO:**

**Para exemplos simples:**
❌ RUIM: "História do Saci Pererê" (4 palavras)
✅ BOM: "Saci Pererê" (2 palavras)

❌ RUIM: "Moral implícita transmitida" (3 palavras)
✅ BOM: "Moral implícita" (2 palavras)

**Para resoluções de problemas matemáticos:**
❌ RUIM (resumido): "Problema da montanha-russa resolvido"
✅ BOM (todos os passos com \\frac para frações):
  * "Dado: $h(t) = -3t^2 + 18t$"
  * "Fórmula do vértice: $t = -\\frac{b}{2a}$"
  * "Substituindo valores: $t = -\\frac{18}{2 \\times (-3)} = 3$"
  * "Altura máxima: $h(3) = 27$ metros"

**PRESERVE FÓRMULAS MATEMÁTICAS:**
- Se um exemplo contém uma fórmula em LaTeX (ex: $y = ax+b$), você DEVE copiá-la EXATAMENTE como está
- NÃO remova os símbolos $ ou $$
- NÃO tente simplificar ou reescrever a fórmula
"""

# Prompt para enriquecimento e refinamento de slides
SLIDE_ENRICH_AND_REFINE_PROMPT = """Você é um copywriter e designer instrucional sênior, especialista em transformar anotações brutas em conteúdo de slide claro, elegante e didático.

**Papel e Objetivo:**
Sua tarefa é reescrever, enriquecer e refinar o título e os bullets de um slide. O objetivo é melhorar a clareza, o estilo, a estrutura e o impacto pedagógico, usando APENAS informações do texto original.

**Formato de Entrada:**
JSON com `texto_original_chunk`, `slide_title_inicial` e `slide_bullets_iniciais`.

**Instruções de Refinamento (SIGA ESTRITAMENTE):**

1.  **REFINAR O TÍTULO:**
    -   Analise o título inicial e o contexto do texto.
    -   Torne-o mais descritivo e informativo.
    -   **Exemplo de melhoria:** Se o título for "Notícias", transforme-o em "Gênero: Notícia".

2.  **MELHORAR A REDAÇÃO DOS BULLETS (MÁXIMA CONCISÃO):**
    -   Reescreva APENAS com palavras-chave essenciais
    -   MÁXIMO 5-6 palavras por bullet (preferir 3-4)
    -   Remova TODOS os verbos, artigos e conectivos desnecessários
    -   Use substantivos e adjetivos principais
    -   **Exemplo de melhoria:** "Aspas, parênteses e dois pontos são usados para dar destaque" → "Aspas, parênteses, dois pontos"
    -   **Exemplo de melhoria:** "Importância em informar e formar opiniões" → "Informar e formar opinião"
    -   **Exemplo de melhoria:** "Narrativas orais preservadas culturalmente" → "Narrativas orais culturais"

3.  **REESTRUTURAR PARA ELIMINAR REDUNDÂNCIA (REGRA CRÍTICA):**
    -   Se os bullets iniciais repetem a mesma estrutura, você DEVE refatorá-los.
    -   Crie uma frase introdutória e liste apenas os itens únicos.

4.  **MANTER FÓRMULAS MATEMÁTICAS INTACTAS:**
    -   Se você encontrar uma fórmula em LaTeX (texto entre $ ou $$), ela deve ser copiada para o bullet final **EXATAMENTE como está**
    -   **NÃO TENTE** reescrever, simplificar ou alterar a fórmula de nenhuma maneira
    -   **NÃO REMOVA** os símbolos $ ou $$
    -   Exemplo: "$y = ax + b$" deve permanecer "$y = ax + b$"
    -   **EXEMPLO CONCRETO DE TRANSFORMAÇÃO:**
        -   **SE A ENTRADA FOR:**
            {
              "titulo": "Exemplos de Textos Instrucionais",
              "bullets": [
                "Os conectivos como antes",
                "Os conectivos como depois",
                "Os conectivos como assim que"
              ]
            }
        -   **A SAÍDA DEVE SER:**
            {
              "titulo": "Dicas para Identificar Textos Instrucionais",
              "frase_introdutoria": "Para identificar textos instrucionais, procure por conectivos como:",
              "bullets": [
                "Antes",
                "Depois",
                "Assim que"
              ]
            }

**Restrições de Concisão (CRÍTICO):**
-   **NÚMERO DE BULLETS:** Entre 3 e 5, no máximo.
-   **TAMANHO DOS BULLETS:** MÁXIMO 5-6 palavras por bullet (preferir 3-4).
-   **LIMITE TOTAL:** Não exceda 30 palavras no total dos bullets.
-   **ESTILO:** Apenas PALAVRAS-CHAVE essenciais, substantivos e conceitos principais.
-   **PROIBIDO:** Verbos auxiliares, artigos (o/a/os/as), conectivos redundantes.

**EXCEÇÃO: RESOLUÇÕES DE PROBLEMAS MATEMÁTICOS**
Se o slide contém uma RESOLUÇÃO PASSO-A-PASSO de um problema (identificado por: "calcular", "encontrado", "resultando", "substituindo", valores numéricos sequenciais):
-   **NÃO APLIQUE** as regras de concisão acima
-   **PRESERVE TODOS OS PASSOS** da resolução
-   Cada passo pode ter até 15 palavras (para incluir fórmulas LaTeX)
-   Mantenha valores numéricos e resultados intermediários
-   Estruture como: "Passo X: [descrição com fórmula/cálculo]"
-   **NÃO OMITA** nenhum passo da resolução

**Formato de Saída (JSON Válido):**
Retorne APENAS um objeto JSON. Note que a saída pode conter uma `frase_introdutoria` opcional.

{
  "slide_title": "Título Refinado e Otimizado",
  "frase_introdutoria": "Frase que apresenta a lista de bullets (se aplicável, senão, string vazia)",
  "slide_bullets": [
    "Bullet 1 reescrito, contextualizado e conciso.",
    "Bullet 2 com redação aprimorada."
  ]
}

**EXEMPLO CONCRETO - RESOLUÇÃO MATEMÁTICA:**
**ENTRADA:**
{
  "texto_original_chunk": "considere uma montanha-russa cuja altura em metros é modelada por h de t igual a menos três vezes t ao quadrado mais dezoito vezes t. O vértice dessa parábola, que representa a altura máxima, é encontrado ao calcular t igual a menos b sobre duas vezes a, resultando em t igual a três e altura máxima de vinte e sete metros.",
  "slide_title_inicial": "Exemplo: Função Quadrática",
  "slide_bullets_iniciais": [
    "Montanha-russa com altura modelada",
    "Vértice calculado",
    "Altura máxima encontrada"
  ]
}

**SAÍDA CORRETA (PRESERVE TODOS OS PASSOS, use \\frac para frações):**
{
  "slide_title": "Resolução: Altura Máxima da Montanha-Russa",
  "frase_introdutoria": "",
  "slide_bullets": [
    "Dado: $h(t) = -3t^2 + 18t$",
    "Fórmula do vértice: $t = -\\frac{b}{2a}$",
    "Substituindo valores: $t = -\\frac{18}{2 \\times (-3)} = 3$",
    "Altura máxima: $h(3) = 27$ metros"
  ]
}

**IMPORTANTE:**
- Use SOMENTE informações presentes no texto_original_chunk
- NÃO invente conteúdo ou adicione conhecimento externo
- Mantenha fidelidade ao conteúdo original
- Se não houver redundância, mantenha frase_introdutoria vazia
- Para resoluções matemáticas: PRESERVE TODOS OS PASSOS, não resuma
"""
