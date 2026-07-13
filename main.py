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

from src.solver.constraints.professor_conflicts import (
    ProfessorConflictConstraint,
)

from src.solver.validators.professor_validator import (
    ProfessorValidator,
)

from src.solver.scheduler import (
    Scheduler,
)

from src.solver.stats import (
    SolverStats,
)

from src.scheduling.schedule_builder import (
    ScheduleBuilder,
)

from src.scheduling.schedule_printer import (
    SchedulePrinter,
)

ARQUIVO = "excel/GERADOR_DE_HORARIOS.xlsx"


def main():

    print()
    print("===== CARREGANDO BASE =====")
    print()

    # -------------------------------------
    # BASE
    # -------------------------------------

    loader = ExcelLoader(
        ARQUIVO
    )

    base = loader.load()

    builder = (
        PedagogicalBlockBuilder(
            base
        )
    )

    base.blocos = (
        builder.build()
    )

    # -------------------------------------
    # REGRAS
    # -------------------------------------

    parser = RuleParser()

    regras = parser.parse(
        base.restricoes
    )

    # -------------------------------------
    # VARIÁVEIS
    # -------------------------------------

    variable_builder = (
        DecisionVariableBuilder(
            base
        )
    )

    model, variables = (
        variable_builder.build()
    )

    # -------------------------------------
    # RULE ENGINE
    # -------------------------------------

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

    # -------------------------------------
    # CONSTRAINTS BASE
    # -------------------------------------

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

    # -------------------------------------
    # ESTATÍSTICAS
    # -------------------------------------

    stats = SolverStats(
        base=base,
        variables=variables,
        resumo_regras=resumo_regras,
        total_block_assignment=total_block_assignment,
        total_turma_conflicts=total_turma_conflicts,
        total_professor_conflicts=total_professor_conflicts,
    )

    stats.imprimir()

    print()
    print("===== REGRAS =====")
    print()

    print(
        "Aplicadas:",
        resumo_regras["aplicadas"]
    )

    print(
        "Pendentes:",
        resumo_regras["pendentes"]
    )

    # -------------------------------------
    # SOLVER
    # -------------------------------------

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

        return

    else:

        print(
            "STATUS:",
            status
        )

        return

    # -------------------------------------
    # VALIDAÇÃO DOCENTE
    # -------------------------------------

    validator = (
        ProfessorValidator(
            base=base,
            variables=variables,
            solver=solver,
        )
    )

    validator.print_report()

    # -------------------------------------
    # HORÁRIO
    # -------------------------------------

    schedule_builder = (
        ScheduleBuilder(
            base=base,
            variables=variables,
            solver=solver,
        )
    )

    schedule = (
        schedule_builder.build()
    )

    SchedulePrinter.print_turma(
        schedule,
        "1ADM01",
    )


if __name__ == "__main__":
    main()