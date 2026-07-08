from src.data.loader import ExcelLoader

from src.builder.pedagogical_blocks import (
    PedagogicalBlockBuilder
)

from src.solver.variables import (
    DecisionVariableBuilder
)

from src.solver.constraints.block_assignment import (
    BlockAssignmentConstraint
)

from src.solver.constraints.turma_conflicts import (
    TurmaConflictConstraint
)


ARQUIVO = "excel/GERADOR_DE_HORARIOS.xlsx"


def main():

    print()
    print("===== CARREGANDO BASE =====")
    print()

    loader = ExcelLoader(
        ARQUIVO
    )

    base = loader.load()

    builder = PedagogicalBlockBuilder(
        base
    )

    base.blocos = builder.build()

    variable_builder = DecisionVariableBuilder(
        base
    )

    model, variables = variable_builder.build()

    block_assignment = BlockAssignmentConstraint(
        model,
        variables,
    )

    total_block_assignment = (
        block_assignment.build()
    )

    turma_conflicts = TurmaConflictConstraint(
        model,
        variables,
        base,
    )

    total_turma_conflicts = (
        turma_conflicts.build()
    )

    print()
    print("===== RESUMO CP-SAT =====")
    print()

    print(
        "Turmas:",
        len(base.turmas)
    )

    print(
        "Blocos:",
        len(base.blocos)
    )

    print(
        "Slots:",
        len(base.slots)
    )

    total_variaveis = 0

    for bloco_id in variables:

        total_variaveis += len(
            variables[bloco_id]
        )

    print(
        "Variáveis CP-SAT:",
        total_variaveis
    )

    print()
    print("===== RESTRIÇÕES =====")
    print()

    print(
        "Block Assignment:",
        total_block_assignment
    )

    print(
        "Turma Conflict:",
        total_turma_conflicts
    )

    print(
        "Total de restrições:",
        total_block_assignment
        + total_turma_conflicts
    )


if __name__ == "__main__":
    main()