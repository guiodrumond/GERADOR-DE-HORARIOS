import argparse
import logging
from pathlib import Path
from datetime import datetime
import threading
import time
from tqdm import tqdm
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
from src.solver.constraints.planejamento_constraint import PlanejamentoConstraint
from src.solver.constraints.atividades_avulsas_constraint import AtividadesAvulsasConstraint
from src.solver.constraints.max_dias_constraint import MaxDiasConstraint
from src.solver.constraints.plan_ind_sliding_window_constraint import PlanIndSlidingWindowConstraint

# Solvers e Relatórios
from src.solver.scheduler import Scheduler
from src.scheduling.schedule_builder import ScheduleBuilder
from src.scheduling.grid_builder import GridBuilder
from src.scheduling.grid_printer import GridPrinter
from src.export.excel_exporter import ExcelExporter
from src.solver.objectives.objective_builder import ObjectiveBuilder
from src.solver.objectives.area_compactness_objective import AreaCompactnessObjective
from src.solver.objectives.teacher_compactness_objective import TeacherCompactnessObjective
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
    
    # Restrições Hard Base
    RuleEngine(model=model, variables=variables, base=base, regras=regras).build()
    BlockAssignmentConstraint(model, variables).build()
    TurmaConflictConstraint(model, variables, base).build()
    ProfessorConflictConstraint(model, variables, base).build()
    PedagogicalPairsConstraint(model, variables, base).build()
    
    # ==========================================================
    # CORREÇÃO DE FLUXO DE DADOS: A HIERARQUIA CORRETA
    # ==========================================================
        
    # Passo A: Cria o planejamento coletivo
    plan_constraint = PlanejamentoConstraint(model, variables, base, analise_atribuicao)
    plan_constraint.build()
        
    # Passo B: Cria o planejamento individual (janela deslizante)
    plan_ind_window = PlanIndSlidingWindowConstraint(model, variables, base, reuniao_vars=plan_constraint.reuniao_vars)
    plan_ind_window.build()
        
    # Passo C: Cria as atividades avulsas (PA / PV)
    AtividadesAvulsasConstraint(model, variables, base).build()
        
    # Passo D: O JUIZ SUPREMO (Max Dias)
    # Agora ele roda por último e recebe TODAS as variáveis para somar!
    MaxDiasConstraint(
        model, 
        variables, 
        base, 
        reuniao_vars=plan_constraint.reuniao_vars,
        plan_ind_vars=plan_ind_window.plan_ind_vars # Passando o PI pro juiz
    ).build()
        
    TeacherAvailabilityConstraint(model, variables, base).build()
    
    objective_builder = ObjectiveBuilder(model, variables, base, regras)

    AreaCompactnessObjective(
        model=model, 
        variables=variables, 
        base=base, 
        regras=regras, 
        objective_builder=objective_builder
    ).build()

    TeacherCompactnessObjective(
        model=model, 
        variables=variables, 
        base=base, 
        regras=regras, 
        objective_builder=objective_builder
    ).build()

    objective_builder.build()
    objective_builder.imprimir_resumo()

    # 5. Solver com Animação de Cronômetro e Medição de Tempo
    logging.info("Executando Solver...")
    scheduler = Scheduler(model, config=getattr(base, 'config', {}))

    def rodar_animacao(evento):
        with tqdm(total=0, desc="🧠 O Solver está pensando", bar_format="{desc} | ⏳ Tempo decorrido: {elapsed}") as pbar:
            while not evento.is_set():
                time.sleep(1)
                pbar.update(1)

    parar_evento = threading.Event()
    t_animacao = threading.Thread(target=rodar_animacao, args=(parar_evento,))
    t_animacao.start()

    inicio_tempo = time.time()
    try:
        solver, status = scheduler.solve()
    finally:
        parar_evento.set()
        t_animacao.join()
    fim_tempo = time.time()
    tempo_decorrido = fim_tempo - inicio_tempo

    if status not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        logging.error(f"Não foi possível encontrar uma solução. STATUS: {status}")
        return
    
    # 6. Relatórios
    schedule = ScheduleBuilder(base=base, variables=variables, solver=solver).build()
    grid = GridBuilder(
        schedule, 
        solver=solver, 
        base=base, 
        reuniao_vars=plan_constraint.reuniao_vars, 
        variables=variables,
        # plan_ind_vars=plan_ind_window.plan_ind_vars
    ).build()

    PedagogicalPairsReporter(solver=solver, variables=variables, base=base, analise_previa=analise_atribuicao).print_report()
    
    # 🔥 CORREÇÃO: Salva a classe na variável e capta os números do terminal
    area_reporter = AreaGroupingReporter(solver=solver, variables=variables, base=base)
    area_reporter.print_report()
    
    # Extrai os dados para o painel do Excel (com trava de segurança caso o método ainda não exista)
    estatisticas = area_reporter.get_stats() if hasattr(area_reporter, 'get_stats') else {}
        
    print(f"\n===== AMOSTRA DE HORÁRIO: {target_turma} =====")
    GridPrinter.print_turma(grid, target_turma)
        
    # ==========================================
    # EXPORTAÇÃO COM PAINEL E TIMESTAMP
    # ==========================================
    logging.info("Exportando o horário gerado para Excel...")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    caminho_saida = f"outputs/horario_gerado_{timestamp}.xlsx"

    try:
        # 🔥 A MÁGICA: Passa as 'estatisticas' capturadas direto para o Exporter!
        exporter = ExcelExporter(base=base, solver=solver, tempo_decorrido=tempo_decorrido, analise_areas=estatisticas) 
        exporter.export(grid=grid, caminho_saida=caminho_saida)
        logging.info(f"✅ Arquivo Excel exportado com sucesso: {caminho_saida}!")
    except Exception as e:
        logging.error(f"Erro crítico ao tentar exportar o Excel: {e}")

    logging.info("Processo finalizado com sucesso.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=str, default="excel/GERADOR_DE_HORARIOS.xlsx")
    parser.add_argument("--turma", type=str, default="1ADM01")
    args = parser.parse_args()
    main(input_excel=args.input, target_turma=args.turma)