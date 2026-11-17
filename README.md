# lgpd-scan

Encontra dado pessoal exposto em código-fonte e diz **qual artigo da LGPD** cada achado toca.

Scanners de segredo existem aos montes. Eles dizem que há uma chave de API no seu código. Nenhum deles diz que aquilo é o Art. 46 da Lei 13.709/2018, que a providência é corrigir e documentar, e que a documentação da correção pesa na dosimetria da sanção pelo Art. 52, §1º, IX.

Essa tradução — do achado técnico para o dispositivo legal — é o que esta ferramenta faz.

---

## Instalação

Requer Python 3.9 ou superior.

```bash
git clone https://github.com/Marcelo-Lucas-Silva/lgpd-scan.git
cd lgpd-scan
pip install -r requirements.txt
```

As dependências servem para ler planilha, documento e PDF. Sem elas o
scanner ainda funciona em código e texto, e pula os demais formatos
com um aviso.

## Uso

```bash
# varre a pasta atual
python -m lgpdscan .

# varre outro projeto
python -m lgpdscan ~/projetos/minha-api

# só o que é grave
python -m lgpdscan . --severidade alto

# relatório para anexar a um parecer
python -m lgpdscan . --formato markdown --saida relatorio.md

# barra o merge se houver achado (integração contínua)
python -m lgpdscan . --falhar

# ver as regras
python -m lgpdscan --listar-regras
```

### Saída

```
cadastro.py
  CRÍTICO linha 15:13  LGPD001  CPF no código-fonte  [529.******25]  →  Art. 46
  CRÍTICO linha 21:9   LGPD006  Credencial no código-fonte  [API_******c"]  →  Art. 46
  ALTO    linha 27:5   LGPD004  Dado pessoal gravado em log  [logg******pf]  →  Art. 6º, VIII
  ALTO    linha 32:10  LGPD005  Dado pessoal sensível tratado  [ra**]  →  Art. 11

17 achado(s) em 2 arquivo(s)
CRÍTICO 5  ALTO 9  MÉDIO 2  BAIXO 1
```

Um exemplo completo de relatório em Markdown está em [`exemplos/relatorio-exemplo.md`](exemplos/relatorio-exemplo.md).

---

## Regras

| Código | Achado | Severidade | Dispositivo |
| --- | --- | --- | --- |
| LGPD001 | CPF exposto | Crítico | Art. 46 |
| LGPD002 | CNPJ exposto | Médio | Art. 46 |
| LGPD003 | E-mail pessoal exposto | Médio | Art. 46 |
| LGPD004 | Dado pessoal gravado em log | Alto | Art. 6º, VIII |
| LGPD005 | Dado pessoal sensível tratado | Alto | Art. 11 |
| LGPD006 | Credencial exposta | Crítico | Art. 46 |
| LGPD007 | Dado pessoal em URL | Alto | Art. 46 |
| LGPD008 | Telefone exposto | Baixo | Art. 46 |
| LGPD009 | Número de cartão exposto | Crítico | Art. 46 |

Para silenciar uma linha específica, escreva nela o comentário `lgpd-scan: ignorar`.

## Formatos lidos

Código e texto (`.py`, `.js`, `.sql`, `.json`, `.csv`, `.md`, …), e também
**planilhas (`.xlsx`), documentos (`.docx`) e PDFs (`.pdf`)** — onde mora a
maior parte do dado pessoal de uma empresa. No relatório, o achado em
documento é localizado em linguagem de pessoa: `Planilha 'Clientes' linha 42`,
`parágrafo 12`, `página 3`.

> **Varra documento na máquina do cliente, não na sua.** Varrer código é ler
> arquivo técnico; varrer a pasta de documentos é ler a base de clientes
> inteira. Rode a ferramenta onde os arquivos já estão e não os copie para
> fora — uma cópia no seu computador faz de você um segundo ponto de exposição.

---

## Três decisões de projeto

**Os documentos são validados, não só reconhecidos.**
Qualquer sequência de onze dígitos parece um CPF — um timestamp em milissegundos, um número de protocolo, um código de barras truncado. O scanner confere os dois dígitos verificadores pelo módulo 11 antes de reportar; cartões passam pelo Luhn e ainda pela faixa de bandeira. A diferença entre uma ferramenta que as pessoas usam e uma que desinstalam no primeiro dia é a taxa de falso positivo, e ela vive nessas funções.

**O relatório mascara o que encontrou.**
Um relatório de LGPD que imprime o CPF por inteiro acabou de criar uma segunda cópia do vazamento — agora num arquivo que circula por e-mail. A saída mostra `529.******25`: suficiente para localizar o dado no arquivo, insuficiente para identificar alguém.

**Código de terceiros não é varrido.**
`node_modules`, `vendor`, `dist`, `.git`. Esses achados não são seus para corrigir, e eles afogam os que são.

---

## O que esta ferramenta NÃO faz

Dizer isto é parte do trabalho, não uma ressalva de rodapé.

A análise é **estática**: lê o código como texto, sem executá-lo. Ela encontra dado pessoal exposto em código-fonte e configuração.

Ela **não** verifica base legal do tratamento, finalidade, necessidade, prazo de retenção, atendimento a direitos do titular, encarregado designado ou transferência internacional. Nada disso é detectável por varredura — exige análise documental e entrevista com as áreas.

**Zero achados não é atestado de conformidade.** É a ausência de uma categoria específica de problema.

---

## Desenvolvimento

```bash
pip install pytest
python -m pytest tests/ -q
```

```
lgpd-scan/
├── lgpdscan/
│   ├── lgpd.py       os artigos e o que cada um exige
│   ├── rules.py      as regras de detecção e os validadores
│   ├── scanner.py    percorre arquivos e aplica as regras
│   ├── report.py     saída de terminal e de parecer
│   └── cli.py        linha de comando
├── tests/
└── exemplos/
    └── loja-ficticia/   código inseguro de propósito, para demonstração
```

### Adicionar uma regra

Uma entrada nova em `REGRAS`, em `lgpdscan/rules.py`. Nada mais no projeto precisa mudar.

```python
Regra(
    codigo="LGPD010",
    nome="Chave PIX no código-fonte",
    descricao="...",
    padrao=re.compile(r"\bpix[_-]?(?:key|chave)\s*[:=]\s*['\"][^'\"]+['\"]"),
    artigo=lgpd.ART_46,
    severidade="alto",
    confirma=None,   # opcional: função que reduz falso positivo
)
```

O campo `confirma` é o que separa uma regra usável de um gerador de ruído. Veja `cpf_valido` e `luhn_valido` em `rules.py` como referência.

---

## Licença

MIT — veja [LICENSE](LICENSE).

Esta ferramenta não substitui parecer jurídico. Ela levanta indícios técnicos; a qualificação jurídica de cada achado depende do contexto do tratamento.
