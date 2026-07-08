from pathlib import Path

from openpyxl import load_workbook

from src.domain.database import BaseDados
from src.domain.models import (
    Curso,
    Turma,
    Especialidade,
    ParPedagogico,
    PadraoPedagogico,
    Slot,
    Restricao,
    Atribuicao,
)


class ExcelLoader:

    def __init__(self, caminho_arquivo: str):

        caminho = Path(caminho_arquivo)

        if not caminho.exists():
            raise FileNotFoundError(
                f"Arquivo não encontrado: {caminho}"
            )

        self.wb = load_workbook(
            filename=caminho,
            data_only=True,
        )

    # ==========================================================
    # UTILITÁRIOS
    # ==========================================================

    def _sheet(self, nome: str):

        if nome not in self.wb.sheetnames:
            raise ValueError(
                f"Aba não encontrada: {nome}"
            )

        return self.wb[nome]

    def _linhas(self, aba: str):

        ws = self._sheet(aba)

        linhas = list(
            ws.iter_rows(values_only=True)
        )

        cabecalho = [
            str(x).strip() if x is not None else ""
            for x in linhas[0]
        ]

        registros = []

        for linha in linhas[1:]:

            if all(
                c is None or str(c).strip() == ""
                for c in linha
            ):
                continue

            registros.append(
                dict(zip(cabecalho, linha))
            )

        return registros

    def _texto(self, valor):

        if valor is None:
            return ""

        return str(valor).strip()

    def _inteiro(self, valor):

        if valor is None:
            return 0

        return int(valor)

    def _booleano(self, valor):

        texto = self._texto(valor).upper()

        return texto in {"S", "SIM", "TRUE", "1"}

    # ==========================================================
    # CONFIG
    # ==========================================================

    def load_config(self):

        config = {}

        for row in self._linhas("CONFIG"):

            parametro = self._texto(
                row["Parâmetro"]
            )

            config[parametro] = row["Valor"]

        return config

    # ==========================================================
    # CURSOS
    # ==========================================================

    def load_cursos(self):

        cursos = []

        for row in self._linhas("CURSOS"):

            cursos.append(
                Curso(
                    nome_curso=self._texto(
                        row["Nome_Curso"]
                    ),
                    codigo=self._texto(
                        row["Curso"]
                    ),
                    especialidade_ftp=self._texto(
                        row["Especialidade_FTP"]
                    ),
                    padrao_ftp=self._texto(
                        row["Padrao_FTP"]
                    ),
                )
            )

        return cursos

    # ==========================================================
    # TURMAS
    # ==========================================================

    def load_turmas(self):

        turmas = []

        for row in self._linhas("TURMAS"):

            turmas.append(
                Turma(
                    codigo=self._texto(
                        row["Turma"]
                    ),
                    curso=self._texto(
                        row["Curso"]
                    ),
                    padrao_ftp=self._texto(
                        row["Padrao_FTP"]
                    ),
                    ativa=self._booleano(
                        row["Ativa"]
                    ),
                )
            )

        return turmas

    # ==========================================================
    # ESPECIALIDADES
    # ==========================================================

    def load_especialidades(self):

        especialidades = []

        for row in self._linhas("ESPECIALIDADES_1ANO"):

            especialidades.append(
                Especialidade(
                    id=self._inteiro(
                        row["Id"]
                    ),
                    componente=self._texto(
                        row["Componente"]
                    ),
                    nome=self._texto(
                        row["Especialidade"]
                    ),
                    sigla=self._texto(
                        row["Sigla"]
                    ),
                    aulas=self._inteiro(
                        row["Aulas"]
                    ),
                )
            )

        return especialidades

    # ==========================================================
    # PARES PEDAGÓGICOS
    # ==========================================================

    def load_pares_pedagogicos(self):

        pares = []

        for row in self._linhas(
            "PARES_PEDAGOGICOS"
        ):

            pares.append(
                ParPedagogico(
                    codigo=self._texto(
                        row["Par"]
                    ),
                    especialidade_1=self._texto(
                        row["Especialidade_1"]
                    ),
                    especialidade_2=self._texto(
                        row["Especialidade_2"]
                    ),
                )
            )

        return pares

    # ==========================================================
    # PADRÕES PEDAGÓGICOS
    # ==========================================================

    def load_padroes_pedagogicos(self):

        padroes = []

        for row in self._linhas(
            "PADROES_PEDAGOGICOS"
        ):

            padroes.append(
                PadraoPedagogico(
                    componente=self._texto(
                        row["Componente"]
                    ),
                    tipo=self._texto(
                        row["Tipo"]
                    ),
                    valor=self._texto(
                        row["Valor"]
                    ),
                )
            )

        return padroes

    # ==========================================================
    # BASE DADOS
    # ==========================================================

    def load(self) -> BaseDados:

        return BaseDados(
            config=self.load_config(),
            cursos=self.load_cursos(),
            turmas=self.load_turmas(),
            especialidades=self.load_especialidades(),
            pares_pedagogicos=self.load_pares_pedagogicos(),
            padroes_pedagogicos=self.load_padroes_pedagogicos(),
            slots=self.load_slots(),
            restricoes=self.load_restricoes(),
            atribuicoes=self.load_atribuicoes(),
        )
    
    def load_slots(self):

        slots = []

        for row in self._linhas("SLOTS"):

            slots.append(
                Slot(
                    dia=self._texto(
                        row["Dia"]
                    ),
                    aula=self._inteiro(
                        row["Aula"]
                    ),
                )
            )

        return slots
    
    # ==========================================================
    # RESTRIÇÕES
    # ==========================================================

    def load_restricoes(self):

        restricoes = []

        for row in self._linhas("RESTRICOES"):

            restricoes.append(
                Restricao(
                    regra=self._texto(
                        row["Regra"]
                    ),
                    valor=self._texto(
                        row["Valor"]
                    ),
                )
            )

        return restricoes
    
    # ==========================================================
    # ATRIBUIÇÕES
    # ==========================================================

    def load_atribuicoes(self):

        atribuicoes = []

        for row in self._linhas("ATRIBUICOES"):

            atribuicoes.append(
                Atribuicao(
                    turma=self._texto(
                        row["Turma"]
                    ),
                    especialidade=self._texto(
                        row["Especialidade"]
                    ),
                    professor=self._texto(
                        row["Professor"]
                    ),
                )
            )

        return atribuicoes
