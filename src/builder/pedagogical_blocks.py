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

    def _tem_padrao(
        self,
        componente: str,
        tipo: str,
    ):

        for padrao in self.base.padroes_pedagogicos:

            if (
                padrao.componente == componente
                and padrao.tipo == tipo
            ):
                return True

        return False

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

        # -------------------------------------------------
        # Componentes individuais
        # -------------------------------------------------

        for esp in self.base.especialidades:

            sigla = esp.sigla.upper()

            if sigla in pares:
                continue

            # PROJETOS

            if sigla == "PROJ":

                blocos.append(
                    BlocoPedagogico(
                        id=f"{turma}_PROJ",
                        turma=turma,
                        componentes=["PROJ"],
                        tamanho=4,
                        fixo=self._tem_padrao(
                            "PROJ",
                            "FIXO",
                        ),
                    )
                )

                continue

            # MATEMÁTICA

            if sigla == "MAT":

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
                            id=(
                                f"{turma}_MAT_"
                                f"{sufixo}"
                            ),
                            turma=turma,
                            componentes=["MAT"],
                            tamanho=2,
                        )
                    )

                continue

            # FTP

            if sigla == "FTP":

                turma_obj = self._buscar_turma(
                    turma
                )

                if turma_obj.padrao_ftp == "BLOCO4":

                    blocos.append(
                        BlocoPedagogico(
                            id=f"{turma}_FTP",
                            turma=turma,
                            componentes=["FTP"],
                            tamanho=4,
                        )
                    )

                elif turma_obj.padrao_ftp == "2+2":

                    blocos.append(
                        BlocoPedagogico(
                            id=f"{turma}_FTP_A",
                            turma=turma,
                            componentes=["FTP"],
                            tamanho=2,
                        )
                    )

                    blocos.append(
                        BlocoPedagogico(
                            id=f"{turma}_FTP_B",
                            turma=turma,
                            componentes=["FTP"],
                            tamanho=2,
                        )
                    )

                continue

            # GEOGRAFIA

            if sigla == "GEO":

                blocos.append(
                    BlocoPedagogico(
                        id=f"{turma}_GEO",
                        turma=turma,
                        componentes=["GEO"],
                        tamanho=2,
                    )
                )

                continue

            # FILOSOFIA

            if sigla == "FIL":

                blocos.append(
                    BlocoPedagogico(
                        id=f"{turma}_FIL",
                        turma=turma,
                        componentes=["FIL"],
                        tamanho=2,
                    )
                )

                continue

            # FÍSICA

            if sigla == "FIS":

                blocos.append(
                    BlocoPedagogico(
                        id=f"{turma}_FIS",
                        turma=turma,
                        componentes=["FIS"],
                        tamanho=2,
                    )
                )

                continue

            # QUÍMICA

            if sigla == "QUI":

                blocos.append(
                    BlocoPedagogico(
                        id=f"{turma}_QUI",
                        turma=turma,
                        componentes=["QUI"],
                        tamanho=2,
                    )
                )

                continue

            # EDUCAÇÃO FÍSICA

            if sigla == "EDF":

                blocos.append(
                    BlocoPedagogico(
                        id=f"{turma}_EDF",
                        turma=turma,
                        componentes=["EDF"],
                        tamanho=2,
                    )
                )

                continue

        # -------------------------------------------------
        # Pares pedagógicos
        # -------------------------------------------------

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

        # -------------------------------------------------
        # Português
        # -------------------------------------------------

        blocos.append(
            BlocoPedagogico(
                id=f"{turma}_POR_A",
                turma=turma,
                componentes=["POR"],
                tamanho=2,
            )
        )

        blocos.append(
            BlocoPedagogico(
                id=f"{turma}_POR_B",
                turma=turma,
                componentes=["POR"],
                tamanho=1,
            )
        )

        return blocos