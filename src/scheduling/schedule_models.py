from dataclasses import dataclass
from collections import defaultdict


@dataclass
class ScheduleEntry:

    turma: str

    dia: str

    aula: int

    bloco_id: str

    componente: str

    professor: str | None = None


class ClassSchedule:

    def __init__(self):

        self.data = defaultdict(dict)

    def add(
        self,
        turma,
        dia,
        aula,
        bloco_id,
        componente,
        professor=None,
    ):

        self.data[turma][
            (dia, aula)
        ] = ScheduleEntry(
            turma=turma,
            dia=dia,
            aula=aula,
            bloco_id=bloco_id,
            componente=componente,
            professor=professor,
        )

    def get(
        self,
        turma,
        dia,
        aula,
    ):

        return self.data[turma].get(
            (dia, aula)
        )

    def turmas(self):

        return sorted(
            self.data.keys()
        )