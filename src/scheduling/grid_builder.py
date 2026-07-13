from src.scheduling.grid_models import (
    Grid,
)


class GridBuilder:

    def __init__(
        self,
        schedule,
    ):

        self.schedule = schedule

    def build(self):

        grid = Grid()

        for turma, agenda in self.schedule.data.items():

            for (
                dia,
                aula,
            ), entry in agenda.items():

                grid.set(
                    turma=turma,
                    dia=dia,
                    aula=aula,
                    texto=entry.componente,
                    bloco_id=entry.bloco_id,
                    professor=entry.professor,
                )

        return grid