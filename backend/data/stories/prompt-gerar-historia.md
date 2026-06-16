# Prompt para gerar histórias (aventuraSolo)

Copie o bloco abaixo e cole em um assistente de IA (ChatGPT, Claude, etc.).
Preencha os campos entre colchetes antes de enviar.

---

## Prompt

```txt
Você é um escritor de ficção interativa especializado em histórias "escolha sua aventura".

Crie uma história completa em JSON para o projeto aventuraSolo, seguindo EXATAMENTE as regras abaixo.

## Parâmetros desta história
- Tema (theme): [ex: fantasy, sci-fi, terror]
- Slug (nome do arquivo, kebab-case): [ex: templo-perdido]
- Título: [ex: O Templo Perdido]
- Sinopse / ideia central: [descreva em 1-3 frases o que a história é sobre]
- Tom: [ex: sombrio, leve, épico, suspense]
- Profundidade desejada: [3 ou 4 níveis de nós, incluindo o rootNode]

## Formato de saída (obrigatório)

Retorne APENAS um objeto JSON válido, sem markdown, sem comentários e sem texto fora do JSON.

Estrutura:

{
  "slug": "kebab-case-igual-ao-nome-do-arquivo",
  "title": "Título da História",
  "theme": "nome-do-tema",
  "rootNode": {
    "content": "Texto narrativo da cena (2-4 frases, em segunda pessoa: 'você')",
    "isEnding": false,
    "isWinningEnding": false,
    "options": [
      {
        "text": "Texto curto da escolha do jogador",
        "nextNode": {
          "content": "...",
          "isEnding": false,
          "isWinningEnding": false,
          "options": [ ... ]
        }
      }
    ]
  }
}

## Regras da árvore de nós

1. rootNode é sempre o ponto de partida (isEnding: false).
2. Nós que NÃO são finais (isEnding: false):
   - Devem ter pelo menos 2 opções (recomendado: 2 ou 3).
   - isWinningEnding deve ser false.
3. Nós finais (isEnding: true):
   - Devem ter "options": [] (array vazio).
   - isWinningEnding: true apenas em finais positivos; false em derrotas ou finais neutros.
4. Cada opção tem "text" (ação do jogador) e "nextNode" (próxima cena).
5. A história deve ter pelo menos 1 final vencedor (isEnding: true E isWinningEnding: true).
6. Deve haver também finais de derrota ou neutros para dar peso às escolhas.
7. Varie o comprimento dos caminhos: alguns finais chegam cedo, outros mais tarde.
8. Nenhum campo de texto pode começar com "SUBSTITUA" — isso invalida o arquivo.

## Regras de conteúdo

- Escreva em português brasileiro.
- Use segunda pessoa ("você") para imergir o jogador.
- Cada "content" deve descrever o que o jogador vê, sente ou o que acontece — não repita o texto da opção.
- Cada "text" de opção deve ser uma ação clara e concisa (máx. ~12 palavras).
- Mantenha coerência narrativa: escolhas levam a consequências lógicas.
- Evite referências a mecânicas de jogo ("você perdeu", "game over"); prefira narrativa imersiva.

## Regras técnicas (validação automática)

- slug, title e theme não podem ser vazios.
- slug deve estar em kebab-case (ex: floresta-perdida).
- theme deve coincidir com a pasta onde o arquivo será salvo (ex: fantasy, sci-fi).
- JSON deve ser parseável: aspas duplas, booleanos em minúsculas (true/false), sem vírgula sobrando.
- Não use campos extras fora da estrutura definida.

## Exemplo de referência (estrutura, não copie o conteúdo)

{
  "slug": "castelo-sombrio",
  "title": "O Castelo Sombrio",
  "theme": "fantasy",
  "rootNode": {
    "content": "Ao anoitecer, você chega às portas de um castelo em ruínas...",
    "isEnding": false,
    "isWinningEnding": false,
    "options": [
      {
        "text": "Entrar pelo salão principal",
        "nextNode": {
          "content": "Dentro do salão, velas acesas sozinhas iluminam tapeçarias rasgadas...",
          "isEnding": false,
          "isWinningEnding": false,
          "options": [
            {
              "text": "Cumprimentar o cavaleiro",
              "nextNode": {
                "content": "O cavaleiro entrega a você uma chave dourada. Você parte vitorioso.",
                "isEnding": true,
                "isWinningEnding": true,
                "options": []
              }
            },
            {
              "text": "Atacar o cavaleiro",
              "nextNode": {
                "content": "Sua lâmina ricocheteia na armadura encantada. Sua jornada termina aqui.",
                "isEnding": true,
                "isWinningEnding": false,
                "options": []
              }
            }
          ]
        }
      }
    ]
  }
}

Gere a história completa agora, respeitando todos os parâmetros e regras acima.
```

---

## Depois de gerar

1. Salve a resposta em `backend/data/stories/{theme}/{slug}.json`
2. Valide antes de usar:

```bash
cd backend
uv run python scripts/validate_story.py data/stories/{theme}/{slug}.json
```

1. Se houver erros, cole a saída do validador de volta na IA e peça correção:

```
O JSON abaixo falhou na validação. Corrija APENAS os problemas listados e devolva o JSON completo corrigido, sem markdown.

Erros:
[cole os erros do validador]

JSON:
[cole o JSON gerado]
```
