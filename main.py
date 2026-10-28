import argparse
import logging
import threading
import time
from datetime import datetime

from ortools.sat.python import cp_model
from tqdm import tqdm

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
from src.solver.constraints.teacher_availability_constraint import TeacherAvailabilityConstraint
from src.solver.constraints.pedagogical_pairs_constraint import PedagogicalPairsConstraint
from src.solver.constraints.planejamento_constraint import PlanejamentoConstraint
from src.solver.constraints.atividades_avulsas_constraint import AtividadesAvulsasConstraint
from src.solver.constraints.max_dias_constraint import MaxDiasConstraint
from src.solver.constraints.plan_ind_sliding_window_constraint import PlanIndSlidingWindowConstraint

from src.solver.scheduler import Scheduler
from src.scheduling.schedule_builder import ScheduleBuilder
from src.scheduling.grid_builder import GridBuilder
from src.scheduling.grid_printer import GridPrinter
from src.export.excel_exporter import ExcelExporter
from src.solver.objectives.objective_builder import ObjectiveBuilder
from src.solver.objectives.area_compactness_objective import AreaCompactnessObjective
from src.solver.objectives.teacher_compactness_objective import TeacherCompactnessObjective
from src.scheduling.pedagogical_reporter import PedagogicalPairsReporter
from src.scheduling.area_grouping_reporter import AreaGroupingReporter
from src.solver.diagnostics.preflight_validator import PreflightValidator
from src.solver.diagnostics.planning_diagnostics import PlanningDiagnostics
from src.solver.diagnostics.planning_mapper import PlanningMapper

# ==========================================================
# PAINEL DE CAMADAS (LIGA / DESLIGA)
# ==========================================================

CAMADAS = {
    # Diagnóstico
    "PREFLIGHT": True,
    "DIAG_PLANEJAMENTO": True,

    # Restrições rígidas
    "RULE_ENGINE": True,
    "CONFLITO_TURMA": True,
    "CONFLITO_PROFESSOR": True,
    "PARES_PEDAGOGICOS": True,
    "DISPONIBILIDADE": True,
    "PLANEJAMENTO_COLETIVO": True,
    "PLANEJAMENTO_INDIVIDUAL": True,
    "ATIVIDADES_AVULSAS": True,
    "MAX_DIAS": True,
    "MAPA_PLANEJAMENTO": True,

    # Objetivos
    "OBJ_COMPACTACAO_AREAS": True,
    "OBJ_COMPACTACAO_PROFESSORES": True,
}

# None = usa o tempo da planilha. Ex.: 600 para testes de 10 minutos.
TEMPO_MAX_TESTE = None


logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")


def ativa(nome):
    return CAMADAS.get(nome, False)


def log_camadas():
    logging.info("=" * 60)
    logging.info("🎛️ CAMADAS DO MODELO")
    logging.info("=" * 60)
    for nome, ligada in CAMADAS.items():
        logging.info(f"   {'🟢 ON ' if ligada else '🔴 OFF'} | {nome}")
    if TEMPO_MAX_TESTE:
        logging.info(f"   ⏱️ Tempo máximo de teste: {TEMPO_MAX_TESTE}s")
    logging.info("=" * 60)


def main(input_excel: str, target_turma: str):

    logging.info("===== INICIANDO GERADOR DE HORÁRIOS =====")
    log_camadas()

    # ======================================================
    # 1. CARREGAMENTO
    # ======================================================

    loader = ExcelLoader(input_excel)
    base = loader.load()
    loader.load_disponibilidade(base, input_excel)

    BaseDadosValidator(base).validate()

    # ======================================================
    # 2. PREFLIGHT
    # ======================================================

    if ativa("PREFLIGHT"):

        preflight = PreflightValidator(base=base)
        problemas = preflight.validate()
        preflight.log_report()

        if problemas:
            logging.error("❌ Pré-validação falhou. O solver não será executado.")
            return

    analise_atribuicao = PedagogicalPairsAnalyzer(base).analisar()

    # ======================================================
    # 3. CONSTRUÇÃO DO MODELO
    # ======================================================

    base.blocos = PedagogicalBlockBuilder(base).build()

    #Mapeamento dos planejamentos coletivos
    if ativa("MAPA_PLANEJAMENTO"):

        reunioes_cabem = PlanningMapper(base).run()

        if not reunioes_cabem and ativa("PLANEJAMENTO_COLETIVO"):
            logging.error("❌ As reuniões não cabem nem sozinhas. O solver principal não será executado.")
            return    

    # Diagnóstico de planejamento (roda mesmo com a camada desligada)
    if ativa("DIAG_PLANEJAMENTO"):

        impossiveis = PlanningDiagnostics(base).log_pre_solver()

        if impossiveis and ativa("PLANEJAMENTO_COLETIVO"):
            logging.error("❌ Planejamento impossível. O solver não será executado.")
            return

    regras = RuleParser().parse(base.restricoes)
    model, variables = DecisionVariableBuilder(base).build()

    # ======================================================
    # 4. RESTRIÇÕES RÍGIDAS
    # ======================================================

    # Base obrigatória: sem ela não existe horário
    BlockAssignmentConstraint(model, variables).build()

    if ativa("RULE_ENGINE"):
        RuleEngine(model=model, variables=variables, base=base, regras=regras).build()

    if ativa("CONFLITO_TURMA"):
        TurmaConflictConstraint(model, variables, base).build()

    if ativa("CONFLITO_PROFESSOR"):
        ProfessorConflictConstraint(model, variables, base).build()

    if ativa("PARES_PEDAGOGICOS"):
        PedagogicalPairsConstraint(model, variables, base).build()

    reuniao_vars = {}
    plan_ind_vars = {}

    if ativa("PLANEJAMENTO_COLETIVO"):
        plan_constraint = PlanejamentoConstraint(model, variables, base, analise_atribuicao)
        plan_constraint.build()
        reuniao_vars = plan_constraint.reuniao_vars

    if ativa("PLANEJAMENTO_INDIVIDUAL"):
        plan_ind_window = PlanIndSlidingWindowConstraint(
            model, variables, base, reuniao_vars=reuniao_vars
        )
        plan_ind_window.build()
        plan_ind_vars = plan_ind_window.plan_ind_vars

    if ativa("ATIVIDADES_AVULSAS"):
        AtividadesAvulsasConstraint(model, variables, base).build()

    if ativa("MAX_DIAS"):
        MaxDiasConstraint(
            model,
            variables,
            base,
            reuniao_vars=reuniao_vars,
            plan_ind_vars=plan_ind_vars,
        ).build()

    if ativa("DISPONIBILIDADE"):
        TeacherAvailabilityConstraint(model, variables, base).build()

    # ======================================================
    # 5. OBJETIVOS
    # ======================================================

    objective_builder = ObjectiveBuilder(model, variables, base, regras)

    if ativa("OBJ_COMPACTACAO_AREAS"):
        AreaCompactnessObjective(
            model=model,
            variables=variables,
            base=base,
            regras=regras,
            objective_builder=objective_builder,
        ).build()

    if ativa("OBJ_COMPACTACAO_PROFESSORES"):
        TeacherCompactnessObjective(
            model=model,
            variables=variables,
            base=base,
            regras=regras,
            objective_builder=objective_builder,
        ).build()

    if ativa("OBJ_COMPACTACAO_AREAS") or ativa("OBJ_COMPACTACAO_PROFESSORES"):
        objective_builder.build()
        objective_builder.imprimir_resumo()
    else:
        logging.info("🎯 Nenhum objetivo ativo: o solver buscará apenas um horário válido.")

    # ======================================================
    # 6. SOLVER
    # ======================================================

    config = dict(getattr(base, "config", {}) or {})

    if TEMPO_MAX_TESTE:
        config["MAX_TIME_SECONDS"] = TEMPO_MAX_TESTE

    scheduler = Scheduler(model, config=config)

    def rodar_animacao(evento):
        with tqdm(
            total=0,
            desc="🧠 O Solver está pensando",
            bar_format="{desc} | ⏳ Tempo decorrido: {elapsed}",
        ) as pbar:
            while not evento.is_set():
                time.sleep(1)
                pbar.update(1)

    parar_evento = threading.Event()
    t_animacao = threading.Thread(target=rodar_animacao, args=(parar_evento,))
    t_animacao.start()

    inicio = time.time()

    try:
        solver, status = scheduler.solve()
    finally:
        parar_evento.set()
        t_animacao.join()

    tempo_decorrido = time.time() - inicio

    if status not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        logging.error(f"Não foi possível encontrar uma solução. STATUS: {status}")
        logging.error(
            "Camadas desligadas neste teste: "
            + (", ".join(n for n, v in CAMADAS.items() if not v) or "nenhuma")
        )
        return

    logging.info(f"✅ Solução encontrada ({status}) em {tempo_decorrido:.1f}s")

    # Reuniões alocadas e professores participantes
    if ativa("DIAG_PLANEJAMENTO") and reuniao_vars:
        PlanningDiagnostics(base).log_pos_solver(solver, reuniao_vars)

    # ======================================================
    # 7. RELATÓRIOS E EXPORTAÇÃO
    # ======================================================

    schedule = ScheduleBuilder(base=base, variables=variables, solver=solver).build()

    grid = GridBuilder(
        schedule,
        solver=solver,
        base=base,
        reuniao_vars=reuniao_vars,
        variables=variables,
    ).build()

    PedagogicalPairsReporter(
        solver=solver,
        variables=variables,
        base=base,
        analise_previa=analise_atribuicao,
    ).print_report()

    area_reporter = AreaGroupingReporter(solver=solver, variables=variables, base=base)
    area_reporter.print_report()

    estatisticas = area_reporter.get_stats() if hasattr(area_reporter, "get_stats") else {}

    print(f"\n===== AMOSTRA DE HORÁRIO: {target_turma} =====")
    GridPrinter.print_turma(grid, target_turma)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    caminho_saida = f"outputs/horario_gerado_{timestamp}.xlsx"

    try:
        ExcelExporter(
            base=base,
            solver=solver,
            tempo_decorrido=tempo_decorrido,
            analise_areas=estatisticas,
        ).export(grid=grid, caminho_saida=caminho_saida)

        logging.info(f"✅ Arquivo Excel exportado: {caminho_saida}")

    except Exception:
        logging.exception("Erro crítico ao exportar o Excel.")
        return

    logging.info("===== PROCESSO FINALIZADO COM SUCESSO =====")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=str, default="excel/GERADOR_DE_HORARIOS.xlsx")
    parser.add_argument("--turma", type=str, default="1ADM01")
    args = parser.parse_args()
    main(input_excel=args.input, target_turma=args.turma)