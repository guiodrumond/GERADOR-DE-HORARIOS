from dataclasses import dataclass
from collections import defaultdict


@dataclass
class ScheduleEntry:

    turma: str

    dia: str

    aula: int

    bloco_id: str

    componentes: list[str]


class ClassSchedule:

    def __init__(self):

        self.data = defaultdict(dict)

    def add(
        self,
        turma,
        dia,
        aula,
        bloco_id,
        componentes,
    ):

        self.data[turma][
            (dia, aula)
        ] = ScheduleEntry(
            turma=turma,
            dia=dia,
            aula=aula,
            bloco_id=bloco_id,
            componentes=componentes,
        )