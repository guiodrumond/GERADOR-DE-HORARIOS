from src.scheduling.schedule_models import (
    ClassSchedule,
)


class ScheduleBuilder:

    def __init__(
        self,
        base,
        variables,
        solver,
    ):

        self.base = base
        self.variables = variables
        self.solver = solver

        self.mapa_professores = (
            self._criar_mapa_professores()
        )

    # ==================================================
    # BUILD
    # ==================================================

    def build(self):

        schedule = ClassSchedule()

        for bloco in self.base.blocos:

            slot_inicio = (
                self._slot_escolhido(
                    bloco.id
                )
            )

            if slot_inicio is None:
                continue

            dia, aula_inicio = (
                self._parse_slot(
                    slot_inicio
                )
            )

            # ----------------------------------
            # PAR PEDAGÓGICO
            # ----------------------------------

            if len(bloco.componentes) == 2:

                componente_1 = (
                    bloco.componentes[0]
                )

                componente_2 = (
                    bloco.componentes[1]
                )

                professor_1 = (
                    self._buscar_professor(
                        bloco.turma,
                        componente_1,
                    )
                )

                professor_2 = (
                    self._buscar_professor(
                        bloco.turma,
                        componente_2,
                    )
                )

                schedule.add(
                    turma=bloco.turma,
                    dia=dia,
                    aula=aula_inicio,
                    bloco_id=bloco.id,
                    componente=componente_1,
                    professor=professor_1,
                )

                schedule.add(
                    turma=bloco.turma,
                    dia=dia,
                    aula=aula_inicio + 1,
                    bloco_id=bloco.id,
                    componente=componente_2,
                    professor=professor_2,
                )

                continue

            # ----------------------------------
            # BLOCO NORMAL
            # ----------------------------------

            componente = (
                bloco.componentes[0]
            )

            professor = (
                self._buscar_professor(
                    bloco.turma,
                    componente,
                )
            )

            for offset in range(
                bloco.tamanho
            ):

                aula = (
                    aula_inicio
                    + offset
                )

                schedule.add(
                    turma=bloco.turma,
                    dia=dia,
                    aula=aula,
                    bloco_id=bloco.id,
                    componente=componente,
                    professor=professor,
                )

        return schedule

    # ==================================================
    # PROFESSORES
    # ==================================================

    def _criar_mapa_professores(self):

        mapa = {}

        for atribuicao in self.base.atribuicoes:

            chave = (
                atribuicao.turma,
                atribuicao.especialidade,
            )

            mapa[chave] = (
                atribuicao.professor
            )

        return mapa

    def _buscar_professor(
        self,
        turma,
        componente,
    ):

        return self.mapa_professores.get(
            (
                turma,
                componente,
            )
        )

    # ==================================================
    # SOLUÇÃO
    # ==================================================

    def _slot_escolhido(
        self,
        bloco_id,
    ):

        for slot_id, var in self.variables[
            bloco_id
        ].items():

            if self.solver.BooleanValue(
                var
            ):
                return slot_id

        return None

    # ==================================================
    # UTIL
    # ==================================================

    def _parse_slot(
        self,
        slot_id,
    ):

        dia, aula = (
            slot_id.split("_")
        )

        return (
            dia,
            int(aula),
        )