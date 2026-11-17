# Relatório de exposição de dados pessoais

**Alvo analisado:** `C:\Users\Admin\projetos\lgpd-scan\exemplos\loja-ficticia`  
**Data da análise:** 16/11/2026  
**Ferramenta:** lgpd-scan  
**Base legal de referência:** Lei 13.709/2018 (LGPD)

## Resumo

| Severidade | Achados |
| --- | --- |
| CRÍTICO | 5 |
| ALTO | 10 |
| MÉDIO | 3 |
| BAIXO | 0 |
| **Total** | **18** |

## Achados

### LGPD001 — CPF exposto

**Severidade:** CRÍTICO  
**Ocorrências:** 1  
**Dispositivo:** Art. 46 — Segurança e sigilo dos dados

Um CPF válido aparece escrito em código, planilha ou documento. O arquivo viaja em backup, e-mail e máquina de quem entra na equipe; o dado viaja junto e ninguém registra esse acesso.

> Os agentes de tratamento devem adotar medidas de segurança, técnicas e administrativas aptas a proteger os dados pessoais de acessos não autorizados e de situações acidentais ou ilícitas.

**Providência:** Corrigir a exposição e documentar a correção. A ANPD considera a adoção de boas práticas na dosimetria da sanção (Art. 52, §1º, IX).

| Arquivo | Localização | Trecho (mascarado) |
| --- | --- | --- |
| `cadastro.py` | linha 15 | `529.******25` |

### LGPD006 — Credencial exposta

**Severidade:** CRÍTICO  
**Ocorrências:** 4  
**Dispositivo:** Art. 46 — Segurança e sigilo dos dados

Chave de API, token ou senha escrita no código. Quem obtém a credencial obtém os dados que ela protege — a exposição não é do segredo, é de tudo que está atrás dele.

> Os agentes de tratamento devem adotar medidas de segurança, técnicas e administrativas aptas a proteger os dados pessoais de acessos não autorizados e de situações acidentais ou ilícitas.

**Providência:** Corrigir a exposição e documentar a correção. A ANPD considera a adoção de boas práticas na dosimetria da sanção (Art. 52, §1º, IX).

| Arquivo | Localização | Trecho (mascarado) |
| --- | --- | --- |
| `cadastro.py` | linha 24 | `API_******0"` |
| `cadastro.py` | linha 25 | `PASS******l"` |
| `config.yml` | linha 11 | `pass******6"` |
| `config.yml` | linha 15 | `api_******0"` |

### LGPD004 — Dado pessoal gravado em log

**Severidade:** ALTO  
**Ocorrências:** 2  
**Dispositivo:** Art. 6º, VIII — Princípio da prevenção

Chamada de log imprimindo variável que carrega dado pessoal. Logs costumam ir para serviço de terceiro, ficam meses e raramente têm controle de acesso próprio.

> Adoção de medidas para prevenir a ocorrência de danos em razão do tratamento de dados pessoais.

**Providência:** Revisar o fluxo antes de ir a produção; o dano aqui é previsível e evitável, o que agrava a responsabilidade.

| Arquivo | Localização | Trecho (mascarado) |
| --- | --- | --- |
| `cadastro.py` | linha 30 | `logg******pf` |
| `cadastro.py` | linha 31 | `prin******il` |

### LGPD005 — Dado pessoal sensível tratado

**Severidade:** ALTO  
**Ocorrências:** 6  
**Dispositivo:** Art. 11 — Dado pessoal sensível

Campo que sugere dado sensível do Art. 5º, II: origem racial, convicção religiosa, opinião política, saúde, vida sexual, genético ou biométrico. Exige base legal específica.

> O tratamento de dados pessoais sensíveis somente poderá ocorrer mediante consentimento específico e destacado do titular, para finalidades específicas, ou nas hipóteses legais do inciso II.

**Providência:** Confirmar a base legal específica para esta categoria. Consentimento genérico de cadastro não serve: tem que ser específico e destacado.

| Arquivo | Localização | Trecho (mascarado) |
| --- | --- | --- |
| `cadastro.py` | linha 35 | `ra**` |
| `cadastro.py` | linha 35 | `ra**` |
| `cadastro.py` | linha 36 | `re******` |
| `cadastro.py` | linha 36 | `re******` |
| `cadastro.py` | linha 37 | `diag******co` |
| `relatorio-lgpd.md` | linha 78 | `reli******sa` |

### LGPD007 — Dado pessoal em URL

**Severidade:** ALTO  
**Ocorrências:** 2  
**Dispositivo:** Art. 46 — Segurança e sigilo dos dados

Dado pessoal passado como parâmetro de URL. Fica no histórico do navegador, no log do servidor, no cabeçalho Referer enviado a terceiros e em qualquer proxy no caminho.

> Os agentes de tratamento devem adotar medidas de segurança, técnicas e administrativas aptas a proteger os dados pessoais de acessos não autorizados e de situações acidentais ou ilícitas.

**Providência:** Corrigir a exposição e documentar a correção. A ANPD considera a adoção de boas práticas na dosimetria da sanção (Art. 52, §1º, IX).

| Arquivo | Localização | Trecho (mascarado) |
| --- | --- | --- |
| `cadastro.py` | linha 44 | `?c***` |
| `cadastro.py` | linha 44 | `&e*****` |

### LGPD002 — CNPJ exposto

**Severidade:** MÉDIO  
**Ocorrências:** 1  
**Dispositivo:** Art. 46 — Segurança e sigilo dos dados

CNPJ não é dado pessoal de pessoa jurídica, mas o de MEI e empresário individual identifica pessoa natural. Trate como dado pessoal até provar o contrário.

> Os agentes de tratamento devem adotar medidas de segurança, técnicas e administrativas aptas a proteger os dados pessoais de acessos não autorizados e de situações acidentais ou ilícitas.

**Providência:** Corrigir a exposição e documentar a correção. A ANPD considera a adoção de boas práticas na dosimetria da sanção (Art. 52, §1º, IX).

| Arquivo | Localização | Trecho (mascarado) |
| --- | --- | --- |
| `config.yml` | linha 5 | `11.2******81` |

### LGPD003 — E-mail pessoal exposto

**Severidade:** MÉDIO  
**Ocorrências:** 2  
**Dispositivo:** Art. 46 — Segurança e sigilo dos dados

Endereço de e-mail real escrito no código. É dado pessoal pelo Art. 5º, I, porque identifica pessoa natural.

> Os agentes de tratamento devem adotar medidas de segurança, técnicas e administrativas aptas a proteger os dados pessoais de acessos não autorizados e de situações acidentais ou ilícitas.

**Providência:** Corrigir a exposição e documentar a correção. A ANPD considera a adoção de boas práticas na dosimetria da sanção (Art. 52, §1º, IX).

| Arquivo | Localização | Trecho (mascarado) |
| --- | --- | --- |
| `cadastro.py` | linha 16 | `joan******br` |
| `config.yml` | linha 6 | `dire******br` |

## Limites desta análise

A varredura é estática: lê o código como texto, sem executá-lo. Ela encontra dado pessoal exposto em código-fonte e configuração. Ela **não** verifica base legal do tratamento, finalidade, necessidade, prazo de retenção, atendimento a direitos do titular nem transferência internacional. Esses pontos exigem análise documental e entrevista com as áreas.

Trechos foram mascarados para que este relatório não se torne, ele próprio, uma nova cópia do dado exposto.