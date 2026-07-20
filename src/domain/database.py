from dataclasses import dataclass
from src.domain.models import (
    Curso, Turma, Professor, Especialidade, ParPedagogico, PadraoPedagogico,
    Atribuicao, BlocoPedagogico, Slot, Restricao, AreaCurso, AfinidadeArea, Peso
)
from dataclasses import dataclass, field

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
    
    # Adicionando os que estavam de fora do construtor:
    professores: list[Professor] = None
    pesos: list[Peso] = None
    areas: list[AreaCurso] = None
    afinidade_areas: list[AfinidadeArea] = None
    blocos: list[BlocoPedagogico] | None = None
    
    # A sua sacada de mestre:
    disponibilidade: dict | None = None

    planejamentos: list = field(default_factory=list)