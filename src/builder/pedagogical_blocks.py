from src.domain.database import BaseDados
from src.domain.models import (
    BlocoPedagogico,
)


class PedagogicalBlockBuilder:

    def __init__(self, base: BaseDados):

        self.base = base

    def _buscar_turma(self, codigo: str):

        for turma in self.base.turmas:

            if turma.codigo == codigo:
                return turma

        raise ValueError(
            f"Turma não encontrada: {codigo}"
        )

    # =====================================================
    # PADRÕES PEDAGÓGICOS
    # =====================================================

    def _valor_padrao(
        self,
        componente: str,
        tipo: str,
    ):

        for padrao in self.base.padroes_pedagogicos:

            if (
                padrao.componente == componente
                and padrao.tipo == tipo
            ):
                return padrao.valor

        return None

    def _numero_duplas_matematica(self):

        valor = self._valor_padrao(
            "MEST",
            "DUPLAS",
        )

        if valor is None:
            return 2

        return int(valor)

    # =====================================================
    # PARES PEDAGÓGICOS
    # =====================================================

    def _componentes_em_pares(self):

        componentes = set()

        for par in self.base.pares_pedagogicos:

            componentes.add(
                par.especialidade_1
            )

            componentes.add(
                par.especialidade_2
            )

        return componentes

    # =====================================================
    # BUILD GERAL
    # =====================================================

    def build(self):

        blocos = []

        for turma in self.base.turmas:

            blocos.extend(
                self._build_turma(
                    turma.codigo
                )
            )

        return blocos

    # =====================================================
    # BUILD POR TURMA
    # =====================================================

    def _build_turma(self, turma: str):

        blocos = []

        pares = self._componentes_em_pares()

        for esp in self.base.especialidades:

            sigla = esp.sigla.upper()

            if sigla in pares:
                continue

            if sigla == "POR":

                blocos.extend(
                    self._criar_portugues(
                        turma
                    )
                )

                continue

            if sigla == "PROJ":

                blocos.append(
                    BlocoPedagogico(
                        id=f"{turma}_PROJ",
                        turma=turma,
                        componentes=["PROJ"],
                        tamanho=4,
                        fixo=True,
                    )
                )

                continue

            if sigla == "MAT":

                blocos.extend(
                    self._criar_matematica(
                        turma
                    )
                )

                continue

            if sigla == "FTP":

                blocos.extend(
                    self._criar_ftp(
                        turma
                    )
                )

                continue

            blocos.extend(
                self._criar_bloco_generico(
                    turma=turma,
                    sigla=sigla,
                    aulas=esp.aulas,
                )
            )

        blocos.extend(
            self._criar_pares_pedagogicos(
                turma
            )
        )

        return blocos

    # =====================================================
    # PORTUGUÊS
    # =====================================================

    def _criar_portugues(self, turma: str):

        return [
            BlocoPedagogico(
                id=f"{turma}_POR_A",
                turma=turma,
                componentes=["POR"],
                tamanho=2,
            ),
            BlocoPedagogico(
                id=f"{turma}_POR_B",
                turma=turma,
                componentes=["POR"],
                tamanho=1,
            ),
        ]

    # =====================================================
    # MATEMÁTICA
    # =====================================================

    def _criar_matematica(self, turma: str):

        blocos = []

        numero_duplas = (
            self._numero_duplas_matematica()
        )

        for numero in range(
            numero_duplas
        ):

            sufixo = chr(
                ord("A") + numero
            )

            blocos.append(
                BlocoPedagogico(
                    id=f"{turma}_MAT_{sufixo}",
                    turma=turma,
                    componentes=["MAT"],
                    tamanho=2,
                )
            )

        return blocos

    # =====================================================
    # FTP
    # =====================================================

    def _criar_ftp(self, turma: str):

        turma_obj = self._buscar_turma(
            turma
        )

        if turma_obj.padrao_ftp == "BLOCO4":

            return [
                BlocoPedagogico(
                    id=f"{turma}_FTP",
                    turma=turma,
                    componentes=["FTP"],
                    tamanho=4,
                )
            ]

        if turma_obj.padrao_ftp == "2+2":

            return [
                BlocoPedagogico(
                    id=f"{turma}_FTP_A",
                    turma=turma,
                    componentes=["FTP"],
                    tamanho=2,
                ),
                BlocoPedagogico(
                    id=f"{turma}_FTP_B",
                    turma=turma,
                    componentes=["FTP"],
                    tamanho=2,
                ),
            ]

        raise ValueError(
            f"Padrao_FTP inválido para turma {turma}: "
            f"{turma_obj.padrao_ftp}"
        )

    # =====================================================
    # PARES PEDAGÓGICOS
    # =====================================================

    def _criar_pares_pedagogicos(self, turma: str):

        blocos = []

        for par in self.base.pares_pedagogicos:

            bloco_id = (
                f"{turma}_"
                f"{par.especialidade_1}_"
                f"{par.especialidade_2}"
            )

            blocos.append(
                BlocoPedagogico(
                    id=bloco_id,
                    turma=turma,
                    componentes=[
                        par.especialidade_1,
                        par.especialidade_2,
                    ],
                    tamanho=2,
                )
            )

        return blocos

    # =====================================================
    # GENÉRICOS
    # =====================================================

    def _criar_bloco_generico(
        self,
        turma: str,
        sigla: str,
        aulas: int,
    ):

        if aulas in {
            1,
            2,
        }:

            return [
                BlocoPedagogico(
                    id=f"{turma}_{sigla}",
                    turma=turma,
                    componentes=[sigla],
                    tamanho=aulas,
                )
            ]

        raise ValueError(
            f"Especialidade {sigla} com {aulas} aulas "
            "não possui regra de blocagem definida."
        )