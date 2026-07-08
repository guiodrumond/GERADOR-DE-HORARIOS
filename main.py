from ortools.sat.python import cp_model

from src.data.loader import ExcelLoader

from src.builder.pedagogical_blocks import (
    PedagogicalBlockBuilder,
)

from src.solver.variables import (
    DecisionVariableBuilder,
)

from src.solver.rules.parser import (
    RuleParser,
)

from src.solver.rules.engine import (
    RuleEngine,
)

from src.solver.constraints.block_assignment import (
    BlockAssignmentConstraint,
)

from src.solver.constraints.turma_conflicts import (
    TurmaConflictConstraint,
)

from src.solver.scheduler import (
    Scheduler,
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

    # =====================================
    # BLOCOS
    # =====================================

    builder = PedagogicalBlockBuilder(
        base
    )

    base.blocos = builder.build()

    # =====================================
    # REGRAS PARAMETRIZADAS
    # =====================================

    parser = RuleParser()

    regras = parser.parse(
        base.restricoes
    )

    # =====================================
    # VARIÁVEIS CP-SAT
    # =====================================

    variable_builder = (
        DecisionVariableBuilder(
            base
        )
    )

    model, variables = (
        variable_builder.build()
    )

    # =====================================
    # RULE ENGINE
    # =====================================

    rule_engine = RuleEngine(
        model=model,
        variables=variables,
        base=base,
        regras=regras,
    )

    total_rule_engine = (
        rule_engine.build()
    )

    resumo_regras = (
        rule_engine.resumo()
    )

    # =====================================
    # CONSTRAINTS BASE
    # =====================================

    block_assignment = (
        BlockAssignmentConstraint(
            model,
            variables,
        )
    )

    total_block_assignment = (
        block_assignment.build()
    )

    turma_conflicts = (
        TurmaConflictConstraint(
            model,
            variables,
            base,
        )
    )

    total_turma_conflicts = (
        turma_conflicts.build()
    )

    # =====================================
    # SOLVER
    # =====================================

    scheduler = Scheduler(
        model
    )

    solver, status = (
        scheduler.solve()
    )

    # =====================================
    # RESUMO
    # =====================================

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
    print("===== RULE ENGINE =====")
    print()

    print(
        "Regras aplicadas:",
        resumo_regras["aplicadas"]
    )

    print(
        "Regras pendentes:",
        resumo_regras["pendentes"]
    )

    print()
    print("===== DIAGNÓSTICO =====")
    print()

    for item in resumo_regras["diagnostico"]:

        print(
            item["alvo"],
            "|",
            item["tipo"],
            "|",
            item["valor"],
            "|",
            item["status"],
            "|",
            item["restricoes_criadas"],
        )

    print()
    print("===== CONSTRAINTS BASE =====")
    print()

    print(
        "Block Assignment:",
        total_block_assignment
    )

    print(
        "Turma Conflict:",
        total_turma_conflicts
    )

    print()
    print("===== SOLVER =====")
    print()

    if status == cp_model.OPTIMAL:

        print(
            "STATUS: OPTIMAL"
        )

    elif status == cp_model.FEASIBLE:

        print(
            "STATUS: FEASIBLE"
        )

    elif status == cp_model.INFEASIBLE:

        print(
            "STATUS: INFEASIBLE"
        )

    else:

        print(
            "STATUS:",
            status
        )

    # =====================================
    # PRIMEIRAS ALOCAÇÕES
    # =====================================

    if status in (
        cp_model.OPTIMAL,
        cp_model.FEASIBLE,
    ):

        print()
        print("===== PRIMEIRAS ALOCAÇÕES =====")
        print()

        contador = 0

        for bloco_id, slots in variables.items():

            for slot_id, variavel in slots.items():

                if solver.BooleanValue(
                    variavel
                ):

                    print(
                        bloco_id,
                        "->",
                        slot_id
                    )

                    contador += 1

                    if contador >= 30:
                        return


if __name__ == "__main__":
    main()