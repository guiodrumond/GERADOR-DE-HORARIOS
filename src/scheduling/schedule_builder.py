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
                    componentes=bloco.componentes,
                )

        return schedule

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