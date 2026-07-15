import argparse
import logging
from pathlib import Path
from ortools.sat.python import cp_model

from src.data.loader import ExcelLoader
from src.data.validators import BaseDadosValidator
from src.data.analyzer import PedagogicalPairsAnalyzer
from src.builder.pedagogical_blocks import PedagogicalBlockBuilder
from src.solver.variables import DecisionVariableBuilder
from src.solver.rules.parser import RuleParser
from src.solver.rules.engine import RuleEngine
from src.solver.constraints.block_assignment_constraint import BlockAssignmentConstraint
from src.solver.constraints.class_conflict_constraint import TurmaConflictConstraint
from src.solver.constraints.professor_conflict_constraint import ProfessorConflictConstraint
from src.solver.scheduler import Scheduler
from src.scheduling.schedule_builder import ScheduleBuilder
from src.scheduling.grid_builder import GridBuilder
from src.scheduling.grid_printer import GridPrinter
from src.export.excel_exporter import ExcelExporter
from src.solver.objectives.objective_builder import ObjectiveBuilder
from src.solver.objectives.area_compactness_objective import AreaCompactnessObjective
from src.solver.planning.planning_window_builder import PlanningWindowBuilder
from src.solver.planning.planning_variables import PlanningVariables
from src.solver.planning.teacher_availability_builder import TeacherAvailabilityBuilder
from src.solver.planning.planning_result_builder import PlanningResultBuilder
from src.solver.constraints.pedagogical_pairs_constraint import PedagogicalPairsConstraint
from src.scheduling.pedagogical_reporter import PedagogicalPairsReporter
from src.scheduling.area_grouping_reporter import AreaGroupingReporter

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")


def main(input_excel: str, target_turma: str):
    logging.info("===== INICIANDO GERADOR DE HORÁRIOS =====")

    base = ExcelLoader(input_excel).load()
    BaseDadosValidator(base).validate()
    
    analyzer = PedagogicalPairsAnalyzer(base)
    analise_atribuicao = analyzer.analisar()
    analyzer.imprimir_avisos_pre_solver(analise_atribuicao)

    base.blocos = PedagogicalBlockBuilder(base).build()

    regras = RuleParser().parse(base.restricoes)
    model, variables = DecisionVariableBuilder(base).build()

    planning_windows = PlanningWindowBuilder(base=base, tamanho_janela=2).build()
    planning_variables = PlanningVariables(model=model, planning_windows=planning_windows, base=base).build()
    
    teacher_availability = TeacherAvailabilityBuilder(
        model=model, variables=variables, base=base, planning_windows=planning_windows
    ).build()

    logging.info(f"Janelas de planejamento criadas: {len(planning_windows)}")

    # O MOTOR DE REGRAS VOLTA (Cuidará de DIAS_DIFERENTES, etc.)
    rule_engine = RuleEngine(model=model, variables=variables, base=base, regras=regras)
    rule_engine.build()
    
    # FÍSICA ESTRUTURAL
    BlockAssignmentConstraint(model, variables).build()
    TurmaConflictConstraint(model, variables, base).build()
    ProfessorConflictConstraint(model, variables, base).build()

    # A NOSSA LEI INEGOCIÁVEL DOS PARES
    PedagogicalPairsConstraint(
        model=model,
        variables=variables,
        base=base,
    ).build()

    # ====================================================
    # SISTEMA DE PREMIAÇÃO (SOFT CONSTRAINTS)
    # ====================================================
    objective_builder = ObjectiveBuilder(
        model=model, variables=variables, base=base, regras=regras
    )
    
    # Injetamos o nosso novo objetivo de compactação de Áreas
    AreaCompactnessObjective(
        model=model,
        variables=variables,
        base=base,
        regras=regras,
        objective_builder=objective_builder,
    ).build()

    # Compila os objetivos no modelo e imprime o resumo
    objective_builder.build()
    objective_builder.imprimir_resumo()

    logging.info("Executando Solver...")
    scheduler = Scheduler(model)
    solver, status = scheduler.solve()

    if status not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        logging.error(f"Não foi possível encontrar uma solução. STATUS: {status}")
        return

    logging.info("Solução encontrada. Validando e extraindo resultados...")

    planning_result = PlanningResultBuilder(
        solver=solver,
        planning_variables=planning_variables,
        planning_windows=planning_windows,
        teacher_availability=teacher_availability,
    ).build()

    schedule = ScheduleBuilder(base=base, variables=variables, solver=solver).build()
    grid = GridBuilder(schedule).build()
    
    PedagogicalPairsReporter(
        solver=solver, 
        variables=variables, 
        base=base,
        analise_previa=analise_atribuicao
    ).print_report()

    schedule = ScheduleBuilder(base=base, variables=variables, solver=solver).build()
    grid = GridBuilder(schedule).build()
    
    # === OS NOSSOS DASHBOARDS DE QUALIDADE ===
    PedagogicalPairsReporter(
        solver=solver, 
        variables=variables, 
        base=base,
        analise_previa=analise_atribuicao
    ).print_report()
    
    AreaGroupingReporter(
        solver=solver,
        variables=variables,
        base=base
    ).print_report()
    # ==========================================
        
    print("\n===== AMOSTRA DE HORÁRIO: 1ADM01 =====")
    GridPrinter.print_turma(grid, "1ADM01")
    
    print("\n===== AMOSTRA DE HORÁRIO: 1ADM02 =====")
    GridPrinter.print_turma(grid, "1ADM02")
    
    print("\n===== EXPORTAÇÃO EXCEL =====")
    output_file = Path("outputs") / "horario_gerado.xlsx"
    
    ExcelExporter(
        base=base,
        planning_result=planning_result,
    ).export(
        grid=grid,
        caminho_saida=str(output_file)
    )
    
    logging.info(f"Processo finalizado com sucesso. Arquivo em: {output_file.resolve()}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Gerador de Horários Escolares usando CP-SAT")
    parser.add_argument("--input", type=str, default="excel/GERADOR_DE_HORARIOS.xlsx", help="Caminho para o Excel de entrada")
    parser.add_argument("--turma", type=str, default="1ADM01", help="Turma para visualização prévia")
    args = parser.parse_args()
    
    main(input_excel=args.input, target_turma=args.turma)