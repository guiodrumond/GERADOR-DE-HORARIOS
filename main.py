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

from src.solver.stats import (
    SolverStats,
)

from src.solver.constraints.professor_conflicts import (
    ProfessorConflictConstraint,
)


ARQUIVO = "excel/GERADOR_DE_HORARIOS.xlsx"


def main():

    # =====================================
    # CARREGAMENTO
    # =====================================

    print()
    print("===== CARREGANDO BASE =====")
    print()

    loader = ExcelLoader(
        ARQUIVO
    )

    base = loader.load()

    # =====================================
    # CONSTRUÇÃO DOS BLOCOS
    # =====================================

    builder = PedagogicalBlockBuilder(
        base
    )

    base.blocos = builder.build()

    # =====================================
    # PARSER DE REGRAS
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

    rule_engine.build()

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

    professor_conflicts = (
        ProfessorConflictConstraint(
            model,
            variables,
            base,
        )
    )

    total_professor_conflicts = (
        professor_conflicts.build()
    )

    # =====================================
    # ESTATÍSTICAS
    # =====================================

    stats = SolverStats(
        base=base,
        variables=variables,
        resumo_regras=resumo_regras,
        total_block_assignment=total_block_assignment,
        total_turma_conflicts=total_turma_conflicts,
        total_professor_conflicts=total_professor_conflicts,
    )

    stats.imprimir()

    # =====================================
    # DIAGNÓSTICO DAS REGRAS
    # =====================================

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

    # =====================================
    # CONSTRAINTS BASE
    # =====================================

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

    print(
        "Professor Conflict:",
        total_professor_conflicts
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
                        slot_id,
                    )

                    contador += 1

                    if contador >= 30:
                        return


if __name__ == "__main__":
    main()