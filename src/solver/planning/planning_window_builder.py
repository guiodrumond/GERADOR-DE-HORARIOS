from src.solver.planning.planning_models import (
    PlanningWindow,
)


class PlanningWindowBuilder:

    def __init__(
        self,
        base,
        tamanho_janela: int = 2,
    ):

        self.base = base
        self.tamanho_janela = tamanho_janela

    def build(self):

        windows = []

        for dia in self._dias():

            aulas = self._aulas_do_dia(
                dia
            )

            for aula_inicio in aulas:

                aula_final = (
                    aula_inicio
                    + self.tamanho_janela
                    - 1
                )

                if aula_final not in aulas:
                    continue

                slots = self._slots_da_janela(
                    dia=dia,
                    aula_inicio=aula_inicio,
                    aula_final=aula_final,
                )

                window_id = (
                    f"{dia}_"
                    f"{aula_inicio}_"
                    f"{aula_final}"
                )

                windows.append(
                    PlanningWindow(
                        id=window_id,
                        dia=dia,
                        aula_inicio=aula_inicio,
                        aula_final=aula_final,
                        slots=slots,
                    )
                )

        return windows

    def _dias(self):

        dias = []

        for slot in self.base.slots:

            if slot.dia not in dias:

                dias.append(
                    slot.dia
                )

        return dias

    def _aulas_do_dia(
        self,
        dia,
    ):

        return sorted(
            [
                slot.aula
                for slot in self.base.slots
                if slot.dia == dia
            ]
        )

    def _slots_da_janela(
        self,
        dia,
        aula_inicio,
        aula_final,
    ):

        slots = []

        for aula in range(
            aula_inicio,
            aula_final + 1,
        ):

            slots.append(
                f"{dia}_{aula}"
            )

        return slots