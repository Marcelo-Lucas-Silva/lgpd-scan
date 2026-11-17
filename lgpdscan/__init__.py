# lgpd-scan - analisador de exposicao de dados pessoais, com mapeamento a LGPD.
# Copyright (C) 2026 Marcelo Lucas Silva
#
# SPDX-License-Identifier: AGPL-3.0-only
# Software livre sob a GNU Affero General Public License v3 (veja LICENSE).
# Licenca comercial alternativa disponivel - veja LICENSING.md.

"""
lgpd-scan — análise estática de exposição de dados pessoais,
com os achados mapeados aos artigos da Lei 13.709/2018.
"""

from .scanner import Achado, varrer, varrer_arquivo
from .rules import REGRAS, Regra

__version__ = "0.1.0"
__all__ = ["Achado", "varrer", "varrer_arquivo", "REGRAS", "Regra"]
