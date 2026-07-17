import argparse
import logging
from pathlib import Path
from ortools.sat.python import cp_model

# Importações principais
from src.data.loader import ExcelLoader
from src.data.validators import BaseDadosValidator
from src.data.analyzer import PedagogicalPairsAnalyzer
from src.builder.pedagogical_blocks import PedagogicalBlockBuilder
from src.solver.variables import DecisionVariableBuilder
from src.solver.rules.parser import RuleParser
from src.solver.rules.engine import RuleEngine

# Restrições
from src.solver.constraints.block_assignment_constraint import BlockAssignmentConstraint
from src.solver.constraints.class_conflict_constraint import TurmaConflictConstraint
from src.solver.constraints.professor_conflict_constraint import ProfessorConflictConstraint
from src.solver.constraints.teacher_availability_constraint import TeacherAvailabilityConstraint
from src.solver.constraints.pedagogical_pairs_constraint import PedagogicalPairsConstraint

# Solvers e Relatórios
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
from src.scheduling.pedagogical_reporter import PedagogicalPairsReporter
from src.scheduling.area_grouping_reporter import AreaGroupingReporter

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

def main(input_excel: str, target_turma: str):
    logging.info("===== INICIANDO GERADOR DE HORÁRIOS =====")

    # 1. Carregamento
    loader = ExcelLoader(input_excel)
    base = loader.load()
    loader.load_disponibilidade(base, input_excel) # Carrega a aba DISPONIBILIDADE
    
    BaseDadosValidator(base).validate()
    
    analyzer = PedagogicalPairsAnalyzer(base)
    analise_atribuicao = analyzer.analisar()
    
    # 2. Construção
    base.blocos = PedagogicalBlockBuilder(base).build()
    regras = RuleParser().parse(base.restricoes)
    model, variables = DecisionVariableBuilder(base).build()

    # 3. Disponibilidade e Restrições
    planning_windows = PlanningWindowBuilder(base=base, tamanho_janela=2).build()
    planning_variables = PlanningVariables(model=model, planning_windows=planning_windows, base=base).build()
    
    # Restrições Hard
    RuleEngine(model=model, variables=variables, base=base, regras=regras).build()
    BlockAssignmentConstraint(model, variables).build()
    TurmaConflictConstraint(model, variables, base).build()
    ProfessorConflictConstraint(model, variables, base).build()
    TeacherAvailabilityConstraint(model, variables, base).build()
    PedagogicalPairsConstraint(model=model, variables=variables, base=base).build()

    # 4. Objetivos (Soft)
    objective_builder = ObjectiveBuilder(model=model, variables=variables, base=base, regras=regras)
    AreaCompactnessObjective(model=model, variables=variables, base=base, regras=regras, objective_builder=objective_builder).build()
    objective_builder.build()
    objective_builder.imprimir_resumo()

    # 5. Solver
    logging.info("Executando Solver...")
    scheduler = Scheduler(model, config=getattr(base, 'config', {}))
    solver, status = scheduler.solve()

    if status not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        logging.error(f"Não foi possível encontrar uma solução. STATUS: {status}")
        return

    # 6. Relatórios
    schedule = ScheduleBuilder(base=base, variables=variables, solver=solver).build()
    grid = GridBuilder(schedule).build()
    
    PedagogicalPairsReporter(solver=solver, variables=variables, base=base, analise_previa=analise_atribuicao).print_report()
    AreaGroupingReporter(solver=solver, variables=variables, base=base).print_report()
        
    print(f"\n===== AMOSTRA DE HORÁRIO: {target_turma} =====")
    GridPrinter.print_turma(grid, target_turma)
    
    logging.info("Processo finalizado com sucesso.")

    # ... código anterior ...
    PedagogicalPairsReporter(solver=solver, variables=variables, base=base, analise_previa=analise_atribuicao).print_report()
    AreaGroupingReporter(solver=solver, variables=variables, base=base).print_report()
        
    # ==========================================
    # EXPORTAÇÃO COM O CAMINHO CORRETO:
    # ==========================================
    logging.info("Exportando o horário gerado para Excel...")
    try:
        exporter = ExcelExporter(base) 
        
        # Coloque 'outputs/' antes do nome do arquivo!
        exporter.export(grid=grid, caminho_saida="outputs/horario_gerado.xlsx")
        
        logging.info("✅ Arquivo Excel exportado com sucesso na pasta 'outputs'!")
    except TypeError:
        exporter = ExcelExporter()
        exporter.export(grid=grid, caminho_saida="outputs/horario_gerado.xlsx")
        logging.info("✅ Arquivo Excel exportado com sucesso na pasta 'outputs'!")
    except Exception as e:
        logging.error(f"Erro crítico ao tentar exportar o Excel: {e}")

    logging.info("Processo finalizado com sucesso.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=str, default="excel/GERADOR_DE_HORARIOS.xlsx")
    parser.add_argument("--turma", type=str, default="1ADM01")
    args = parser.parse_args()
    main(input_excel=args.input, target_turma=args.turma)