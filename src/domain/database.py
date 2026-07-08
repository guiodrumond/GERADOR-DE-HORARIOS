from dataclasses import dataclass

from src.domain.models import (
    Curso,
    Turma,
    Especialidade,
)


@dataclass
class BaseDados:

    config: dict

    cursos: list[Curso]

    turmas: list[Turma]

    especialidades: list[Especialidade]

    pares_pedagogicos: list[ParPedagogico]

    padroes_pedagogicos: list[PadraoPedagogico]

    blocos: list[BlocoPedagogico] | None = None

    slots: list[Slot] | None = None


from src.domain.models import (
    Curso,
    Turma,
    Especialidade,
    BlocoPedagogico,
    ParPedagogico,
    PadraoPedagogico,
    Slot
)