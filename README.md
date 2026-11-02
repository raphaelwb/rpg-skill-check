
# RPG Skill Check

Minigame independente para Telegram Web Apps, criado para ser integrado a sistemas de RPG.

Atualmente possui dois métodos:

- **Number:** rolagem de um número dentro de um intervalo.
- **Sequence:** memorizar e reproduzir uma sequência de direções.

## Estrutura

```text
rpg-skill-check/
├── game/
│   └── index.html
├── bot/
│   ├── main.py
│   └── skill_check.py
├── .env.example
├── .gitignore
├── requirements.txt
└── README.md
```

## Configuração

1. Copie `.env.example` para `.env`.
2. Preencha `BOT_TOKEN` com o token do seu bot.
3. Configure `GAME_URL` com a URL do jogo publicado.

Exemplo:

```env
BOT_TOKEN=123456:SEU_TOKEN
GAME_URL=https://seu-usuario.github.io/rpg-skill-check/game

NUMBER_MIN=1
NUMBER_MAX=100

SEQUENCE_LENGTH=5
SEQUENCE_DISPLAY_TIME=2000
SEQUENCE_TIME_LIMIT=15000
```

Não envie o arquivo `.env` para o GitHub.

## Publicação no GitHub Pages

1. Abra as configurações do repositório.
2. Acesse **Pages**.
3. Selecione **Deploy from a branch**.
4. Escolha a branch `main`.
5. Escolha a pasta `/ (root)`.
6. Salve.

O endereço do jogo será semelhante a:

```text
https://seu-usuario.github.io/rpg-skill-check/game/
```

Use esse endereço em `GAME_URL`.

## Instalação do bot

Recomendado Python 3.10 ou superior.

Crie e ative um ambiente virtual:

```bash
python -m venv .venv
```

Linux:

```bash
source .venv/bin/activate
```

Windows:

```bash
.venv\Scripts\activate
```

Instale as dependências:

```bash
pip install -r requirements.txt
```

Inicie o bot:

```bash
python bot/main.py
```

## Comandos do Telegram

| Comando | Descrição |
|---|---|
| `/start` | Exibe os dois botões |
| `/basico` | Exibe os botões usando o intervalo padrão |
| `/basico 10 50` | Configura o intervalo numérico de 10 a 50 |
| `/sequencia` | Usa as configurações padrão da sequência |
| `/sequencia 7` | Usa 7 direções |
| `/sequencia 7 20000` | Usa 7 direções e 20 segundos |

Os parâmetros informados nos comandos prevalecem sobre os valores do `.env`.

## Configurações

| Variável | Padrão | Descrição |
|---|---:|---|
| `NUMBER_MIN` | 1 | Menor número |
| `NUMBER_MAX` | 100 | Maior número |
| `SEQUENCE_LENGTH` | 5 | Quantidade de direções |
| `SEQUENCE_DISPLAY_TIME` | 2000 | Tempo de visualização em ms |
| `SEQUENCE_TIME_LIMIT` | 15000 | Tempo para executar em ms |

## Resultado do teste numérico

Exemplo:

```json
{
  "type": "skill_check",
  "method": "number",
  "minimum": 1,
  "maximum": 100,
  "result": 42
}
```

## Resultado do teste de sequência

Exemplo:

```json
{
  "type": "skill_check",
  "method": "sequence",
  "challenge_id": "abc123",
  "inputs": ["UP", "LEFT", "DOWN", "RIGHT", "UP"],
  "time_ms": 8420
}
```

O bot compara as entradas com a sequência original e calcula o sucesso e a quantidade de direções corretas.

## Observações de segurança

- O bot guarda a sequência esperada e valida as entradas recebidas.
- Cada desafio de sequência só pode ser utilizado uma vez.
- O tempo é medido no navegador com `performance.now()`, evitando penalizar o jogador pela latência da comunicação.
- O tempo informado pelo navegador não pode ser comprovado criptograficamente pelo bot.
- O resultado numérico também é gerado no navegador e não deve ser considerado seguro contra manipulação.
- Os desafios pendentes são armazenados em memória. Reiniciar o bot invalida os desafios que ainda não foram concluídos.

Esta versão é voltada a testes e prototipagem.
