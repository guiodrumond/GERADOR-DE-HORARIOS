from src.data.loader import ExcelLoader

from src.builder.pedagogical_blocks import (
    PedagogicalBlockBuilder
)

from src.solver.variables import (
    DecisionVariableBuilder
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
    print("===== AMOSTRA DE VARIÁVEIS =====")
    print()

    contador = 0

    for bloco_id, slots in variables.items():

        print(
            bloco_id,
            "->",
            len(slots),
            "slots possíveis"
        )

        primeiros_slots = list(
            slots.keys()
        )[:5]

        print(
            "   ",
            primeiros_slots
        )

        contador += 1

        if contador == 10:
            break


if __name__ == "__main__":
    main()