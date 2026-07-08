from src.domain.database import BaseDados
from src.domain.models import (
    BlocoPedagogico,
)


class PedagogicalBlockBuilder:

    def __init__(self, base: BaseDados):

        self.base = base

    def build(self):

        blocos = []

        for turma in self.base.turmas:

            blocos.extend(
                self._build_turma(
                    turma.codigo
                )
            )

        return blocos

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

    def _build_turma(self, turma: str):

        blocos = []

        pares = self._componentes_em_pares()

        # =====================================================
        # ESPECIALIDADES INDIVIDUAIS
        # =====================================================

        for esp in self.base.especialidades:

            sigla = esp.sigla.upper()

            # Componentes que pertencem a pares
            # serão criados depois

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
                        fixo=True,
                    )
                )

                continue

            # MATEMÁTICA

            if sigla == "MAT":

                blocos.append(
                    BlocoPedagogico(
                        id=f"{turma}_MAT_A",
                        turma=turma,
                        componentes=["MAT"],
                        tamanho=2,
                    )
                )

                blocos.append(
                    BlocoPedagogico(
                        id=f"{turma}_MAT_B",
                        turma=turma,
                        componentes=["MAT"],
                        tamanho=2,
                    )
                )

                continue

            # FTP

            if sigla == "FTP":

                blocos.append(
                    BlocoPedagogico(
                        id=f"{turma}_FTP",
                        turma=turma,
                        componentes=["FTP"],
                        tamanho=4,
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

        # =====================================================
        # PARES PEDAGÓGICOS
        # =====================================================

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

        # =====================================================
        # PORTUGUÊS
        # =====================================================

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