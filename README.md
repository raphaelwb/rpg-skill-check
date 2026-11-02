
# RPG Skill Roll

Minigame independente para rolagens de habilidade integrado ao Telegram Mini Apps.

O RPG Skill Roll é responsável apenas por gerar e devolver um resultado numérico. A interpretação desse resultado, aplicação de atributos, modificadores e regras de combate ficam sob responsabilidade do RPG que utilizar o módulo.

## Estrutura do projeto

```text
rpg-skill-roll/
├── game/
│   └── index.html
├── bot/
│   └── main.py
├── .env
├── .gitignore
├── requirements.txt
└── README.md
```

## Requisitos

- Python 3.10 ou superior.
- Um bot criado pelo [@BotFather](https://t.me/BotFather).
- Hospedagem HTTPS para o minigame.

## Configuração

### 1. Criar o arquivo `.env`

Na raiz do projeto, crie um arquivo chamado `.env`:

```dotenv
BOT_TOKEN=SEU_TOKEN_DO_TELEGRAM
GAME_URL=https://raphaelwb.github.io/skill-roll/game/
```

**Variáveis disponíveis:**

| Variável | Descrição |
|---|---|
| `BOT_TOKEN` | Token fornecido pelo BotFather. |
| `GAME_URL` | Endereço HTTPS onde o minigame está hospedado. |

Não compartilhe seu arquivo `.env` nem envie seu token para o GitHub.

### 2. Publicar o minigame

Publique o conteúdo da pasta `game` em uma hospedagem estática com HTTPS.

Exemplo usando GitHub Pages:

```text
https://raphaelwb.github.io/skill-roll/game/
```

O endereço publicado deve apontar para o `index.html`.

### 3. Instalar as dependências

Na raiz do projeto, execute:

```bash
pip install -r requirements.txt
```

O projeto utiliza:

- `python-telegram-bot`: integração com o Telegram.
- `python-dotenv`: leitura das configurações do arquivo `.env`.

### 4. Executar o bot

Na raiz do projeto, execute:

```bash
python bot/main.py
```

Se as configurações estiverem corretas, o terminal exibirá:

```text
RPG Skill Roll iniciado.
```

Abra o bot no Telegram e envie:

```text
/start
```

O bot apresentará o botão para abrir o minigame.

## Configuração das rolagens

A faixa numérica é configurada por parâmetros na URL.

Exemplos:

| Finalidade | Parâmetros |
|---|---|
| Padrão | `?min=1&max=100` |
| Faixa curta | `?min=1&max=20` |
| Perícia | `?min=1&max=50` |
| Personalizada | `?min=10&max=200` |

Os valores mínimo e máximo são inclusivos.

## Dados retornados

Após a rolagem, o minigame envia ao bot um objeto JSON:

```json
{
  "type": "skill_roll",
  "result": 75,
  "min": 1,
  "max": 100
}
```

### Significado dos campos

| Campo | Descrição |
|---|---|
| `type` | Identifica o tipo de operação. |
| `result` | Número sorteado. |
| `min` | Limite mínimo utilizado. |
| `max` | Limite máximo utilizado. |

## Integração com RPGs

O RPG Skill Roll não possui regras próprias de combate ou atributos.

O RPG pode utilizar o resultado recebido para realizar seus próprios cálculos.

Exemplo:

```python
resultado = 75
forca = 20
bonus = 10

habilidade_final = resultado + forca + bonus

print(habilidade_final)
```

## Segurança

A primeira versão realiza o sorteio no navegador.

Isso significa que um cliente modificado pode manipular o resultado enviado ao bot.

Para utilização competitiva ou em partidas que exigem integridade, recomenda-se:

- Validar a identidade do usuário utilizando os dados de inicialização do Telegram (`initData`).
- Realizar o sorteio no servidor.
- Não confiar exclusivamente nos valores enviados pelo navegador.

## Licença

Defina a licença de distribuição conforme as necessidades do projeto.
```

**Observação:** o `.env` deve permanecer fora do repositório. O `.gitignore` já deve conter essa proteção.