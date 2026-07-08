from src.data.loader import ExcelLoader

from src.builder.pedagogical_blocks import (
    PedagogicalBlockBuilder,
)

from src.solver.variables import (
    DecisionVariableBuilder,
)

from src.solver.constraints.block_assignment import (
    BlockAssignmentConstraint,
)


ARQUIVO = "excel/GERADOR_DE_HORARIOS.xlsx"


def main():

    print()
    print("===== CARREGANDO BASE =====")
    print()

    loader = ExcelLoader(ARQUIVO)

    base = loader.load()

    builder = PedagogicalBlockBuilder(base)

    base.blocos = builder.build()

    variable_builder = DecisionVariableBuilder(
        base
    )

    model, variables = variable_builder.build()

    constraint = BlockAssignmentConstraint(
        model,
        variables,
    )

    total_restricoes = constraint.build()

    print()
    print("===== RESTRIÇÕES =====")
    print()

    print(
        "Block Assignment:",
        total_restricoes,
    )

if __name__ == "__main__":
    main()