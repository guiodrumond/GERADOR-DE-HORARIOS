from dataclasses import dataclass

from src.domain.models import (
    Curso,
    Turma,
    Especialidade,
    ParPedagogico,
    PadraoPedagogico,
    Atribuicao,
    BlocoPedagogico,
    Slot,
    Restricao,
)


@dataclass
class BaseDados:

    config: dict

    cursos: list[Curso]

    turmas: list[Turma]

    especialidades: list[Especialidade]

    pares_pedagogicos: list[ParPedagogico]

    padroes_pedagogicos: list[PadraoPedagogico]

    restricoes: list[Restricao]

    atribuicoes: list[Atribuicao]

    slots: list[Slot]

    blocos: list[BlocoPedagogico] | None = None