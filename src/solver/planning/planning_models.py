from dataclasses import dataclass


@dataclass(frozen=True)
class PlanningWindow:

    id: str

    dia: str

    aula_inicio: int

    aula_final: int

    slots: list[str]