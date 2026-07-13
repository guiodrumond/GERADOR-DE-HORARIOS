from pathlib import Path

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

from src.scheduling.grid_builder import (
    GridBuilder,
)

from src.scheduling.grid_printer import (
    GridPrinter,
)

from src.export.excel_exporter import (
    ExcelExporter,
)

from src.solver.objectives.objective_builder import (
    ObjectiveBuilder,
)

from src.solver.objectives.area_grouping_objective import (
    AreaGroupingObjective,
)

from src.solver.validators.area_continuity_validator import (
    AreaContinuityValidator,
)

from src.solver.objectives.area_compactness_objective import (
    AreaCompactnessObjective,
)

from src.solver.planning.planning_window_builder import (
    PlanningWindowBuilder,
)

ARQUIVO = "excel/GERADOR_DE_HORARIOS.xlsx"


def main():

    print()
    print("===== GERADOR DE HORÁRIOS =====")
    print()

    # ====================================================
    # CARREGAMENTO
    # ====================================================

    loader = ExcelLoader(
        ARQUIVO
    )

    base = loader.load()

    planning_windows = (
    PlanningWindowBuilder(
        base=base,
        tamanho_janela=2,
    ).build()
    )

    print()
    print("===== JANELAS DE PLANEJAMENTO =====")
    print()

    print(
        "Total:",
        len(planning_windows)
    )

    for window in planning_windows:

        print(
            window.id,
            "|",
            window.dia,
            "|",
            window.aula_inicio,
            "-",
            window.aula_final,
            "|",
            window.slots,
        )

    # ====================================================
    # BLOCOS PEDAGÓGICOS
    # ====================================================

    builder = PedagogicalBlockBuilder(
        base
    )

    base.blocos = builder.build()

    # ====================================================
    # REGRAS PARAMETRIZADAS
    # ====================================================

    parser = RuleParser()

    regras = parser.parse(
        base.restricoes
    )

    # ====================================================
    # VARIÁVEIS CP-SAT
    # ====================================================

    variable_builder = (
        DecisionVariableBuilder(
            base
        )
    )

    model, variables = (
        variable_builder.build()
    )

    # ====================================================
    # RULE ENGINE
    # ====================================================

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

    # ====================================================
    # CONSTRAINTS BASE
    # ====================================================

    total_block_assignment = (
        BlockAssignmentConstraint(
            model,
            variables,
        ).build()
    )

    total_turma_conflicts = (
        TurmaConflictConstraint(
            model,
            variables,
            base,
        ).build()
    )

    total_professor_conflicts = (
        ProfessorConflictConstraint(
            model,
            variables,
            base,
        ).build()
    )

    # ====================================================
    # OBJECTIVE BUILDER
    # ====================================================

    objective_builder = ObjectiveBuilder(
        model=model,
        variables=variables,
        base=base,
        regras=regras,
    )

    area_compactness = AreaCompactnessObjective(
        model=model,
        variables=variables,
        base=base,
        regras=regras,
        objective_builder=objective_builder,
    )

    total_area_compactness_terms = (
        area_compactness.build()
    )

    total_objective_terms = (
        objective_builder.build()
    )

    objective_builder.imprimir_resumo()


    # ====================================================
    # ESTATÍSTICAS
    # ====================================================

    stats = SolverStats(
        base=base,
        variables=variables,
        resumo_regras=resumo_regras,
        total_block_assignment=total_block_assignment,
        total_turma_conflicts=total_turma_conflicts,
        total_professor_conflicts=total_professor_conflicts,
    )

    stats.imprimir()

    # ====================================================
    # SOLVER
    # ====================================================

    print()
    print("===== EXECUTANDO SOLVER =====")
    print()

    scheduler = Scheduler(
        model
    )

    solver, status = (
        scheduler.solve()
    )

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
            status,
        )

        return

    # ====================================================
    # VALIDAÇÃO DOCENTE
    # ====================================================

    validator = (
        ProfessorValidator(
            base=base,
            variables=variables,
            solver=solver,
        )
    )

    validator.print_report()

    # ====================================================
    # SCHEDULE
    # ====================================================

    print()
    print("===== CONSTRUINDO SCHEDULE =====")
    print()

    schedule = (
        ScheduleBuilder(
            base=base,
            variables=variables,
            solver=solver,
        ).build()
    )

    # ====================================================
    # GRID
    # ====================================================

    print()
    print("===== CONSTRUINDO GRADE =====")
    print()

    grid = (
        GridBuilder(
            schedule
        ).build()
    )

    print(
        "Turmas na grade:",
        len(
            grid.turmas()
        )
    )

    print(
        "Células preenchidas:",
        grid.total_cells()
    )

    area_validator = AreaContinuityValidator(
        base=base,
        grid=grid,
        regras=regras,
    )

    area_validator.print_report()

    # ====================================================
    # VISUALIZAÇÃO
    # ====================================================

    print()
    print("===== AMOSTRA DE HORÁRIO =====")

    GridPrinter.print_turma(
        grid,
        "1ADM01",
    )

    # ====================================================
    # EXPORTAÇÃO EXCEL
    # ====================================================

    print()
    print("===== EXPORTAÇÃO EXCEL =====")
    print()

    output_file = (
        Path("outputs")
        / "horario_gerado.xlsx"
    )

    exporter = ExcelExporter(
        base
    )

    exporter.export(
        grid=grid,
        caminho_saida=str(
            output_file
        ),
    )

    print(
        "Arquivo gerado:"
    )

    print(
        output_file.resolve()
    )

    print()
    print("===== PROCESSO FINALIZADO =====")


if __name__ == "__main__":
    main()