import argparse
import logging
import threading
import time
from collections import defaultdict
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
    "DIAG_DIAS_TRAVADOS": True,
    "DIAG_PLANEJAMENTO": True,
    "MAPA_PLANEJAMENTO": True,
    "DIAG_DIAS_USADOS": True,

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
    "MAX_DIAS_FLEXIVEL": False,   # True = excesso vira penalidade | False = limite rígido

    # Objetivos
    "OBJ_COMPACTACAO_AREAS": False,
    "OBJ_COMPACTACAO_PROFESSORES": False,
}

# None = usa o tempo da planilha. Ex.: 600 para testes de 10 minutos.
TEMPO_MAX_TESTE = 600

# Peso de cada dia acima do Max Dias (bem maior que os pesos de compactação)
PESO_EXCESSO_DIAS = 10000


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


def mapear_dias_pa_pv(base):

    try:
        return MaxDiasConstraint(
            None,
            {},
            base,
            reuniao_vars={},
            plan_ind_vars={},
        )._mapear_fantasmas()
    except Exception:
        logging.exception("❌ Não foi possível mapear os dias de PA/PV.")
        return None


def diagnosticar_dias_travados(base):

    logging.info("=" * 60)
    logging.info("📆 DIAS TRAVADOS POR PA/PV x MAX DIAS")
    logging.info("=" * 60)

    fantasmas = mapear_dias_pa_pv(base)

    if fantasmas is None:
        return

    logging.info(f"   Professores com PA/PV mapeado: {len(fantasmas)}")

    criticos = 0

    for prof in base.professores:

        nome = str(prof.nome).strip().upper()
        travados = fantasmas.get(nome, set())

        try:
            max_dias = int(float(prof.max_dias))
        except (TypeError, ValueError):
            continue

        livres = max_dias - len(travados)

        if livres <= 1:
            criticos += 1
            logging.warning(
                f"   ⚠️ {nome} | Max Dias: {max_dias} "
                f"| Travados por PA/PV: {sorted(travados)} "
                f"| Livres p/ aulas e reuniões: {livres}"
            )

    if criticos:
        logging.warning(f"   Professores com 1 dia livre ou menos: {criticos}")
    else:
        logging.info("   ✅ Nenhum professor com dias críticos.")

    logging.info("=" * 60)


def diagnosticar_dias_usados(base, grid, solver, reuniao_vars):

    logging.info("=" * 60)
    logging.info("📆 DIAS USADOS x MAX DIAS (aulas + reuniões + PA/PV)")
    logging.info("=" * 60)

    dias_aulas = defaultdict(set)
    dias_reunioes = defaultdict(set)
    dias_pa_pv = defaultdict(set)

    # 1. Aulas do horário gerado
    for turma in base.turmas:

        codigo = turma.codigo

        for slot in base.slots:

            try:
                cell = grid.get(codigo, slot.dia, slot.aula)
            except Exception:
                cell = None

            professor = getattr(cell, "professor", None) if cell else None

            if professor:
                dias_aulas[str(professor).strip().upper()].add(
                    str(slot.dia).strip().upper()
                )

    # 2. Reuniões alocadas, só para os convocados
    if reuniao_vars:

        diag = PlanningDiagnostics(base)
        planos = {p.nome: p for p in getattr(base, "planejamentos", []) or []}

        for nome, slots in reuniao_vars.items():

            dias_ativos = {
                slot_id.split("_")[0].strip().upper()
                for slot_id, var in slots.items()
                if solver.Value(var) == 1
            }

            plan = planos.get(nome)

            if not plan:
                continue

            for prof in diag._participantes(plan):
                dias_reunioes[prof] |= dias_ativos

    # 3. PA/PV do ano em que atua
    fantasmas = mapear_dias_pa_pv(base) or {}

    for prof, dias in fantasmas.items():
        dias_pa_pv[str(prof).strip().upper()] |= {
            str(d).strip().upper() for d in dias
        }

    # 4. Comparação com Max Dias
    limites = {}

    for p in base.professores:
        try:
            limites[str(p.nome).strip().upper()] = int(float(p.max_dias))
        except (TypeError, ValueError):
            continue

    estouros = 0

    for prof in sorted(limites):

        limite = limites[prof]

        aulas = dias_aulas.get(prof, set())
        reunioes = dias_reunioes.get(prof, set())
        pa_pv = dias_pa_pv.get(prof, set())

        total = aulas | reunioes | pa_pv

        if len(total) > limite:
            estouros += 1
            logging.warning(
                f"   ⚠️ {prof} | Max Dias: {limite} | Usados: {len(total)} {sorted(total)} "
                f"| Aulas: {sorted(aulas)} | Reuniões: {sorted(reunioes)} | PA/PV: {sorted(pa_pv)}"
            )

    if estouros:
        logging.warning(f"   Professores acima do Max Dias: {estouros} de {len(limites)}")
    else:
        logging.info("   ✅ Nenhum professor passou do Max Dias nesta solução.")

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

    if ativa("DIAG_DIAS_TRAVADOS"):
        diagnosticar_dias_travados(base)

    # ======================================================
    # 3. CONSTRUÇÃO DO MODELO
    # ======================================================

    base.blocos = PedagogicalBlockBuilder(base).build()

    # Mapeamento dos planejamentos coletivos
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

    max_dias_constraint = None

    if ativa("MAX_DIAS"):
        max_dias_constraint = MaxDiasConstraint(
            model,
            variables,
            base,
            reuniao_vars=reuniao_vars,
            plan_ind_vars=plan_ind_vars,
            flexivel=ativa("MAX_DIAS_FLEXIVEL"),
        )
        max_dias_constraint.build()

    if ativa("DISPONIBILIDADE"):
        TeacherAvailabilityConstraint(model, variables, base).build()

    # ======================================================
    # 5. OBJETIVOS
    # ======================================================

    objective_builder = ObjectiveBuilder(model, variables, base, regras)
    usar_objetivo = False

    if ativa("OBJ_COMPACTACAO_AREAS"):
        AreaCompactnessObjective(
            model=model,
            variables=variables,
            base=base,
            regras=regras,
            objective_builder=objective_builder,
        ).build()
        usar_objetivo = True

    if ativa("OBJ_COMPACTACAO_PROFESSORES"):
        TeacherCompactnessObjective(
            model=model,
            variables=variables,
            base=base,
            regras=regras,
            objective_builder=objective_builder,
        ).build()
        usar_objetivo = True

    # Penalidade de excesso de dias (Max Dias flexível)
    if max_dias_constraint and max_dias_constraint.flexivel and max_dias_constraint.excessos:

        for prof, info in max_dias_constraint.excessos.items():
            objective_builder.add_term(
                expression=info["var"],
                peso=-PESO_EXCESSO_DIAS,
                descricao=f"EXCESSO DIAS {prof}",
            )

        usar_objetivo = True

        logging.info(
            f"⚖️ Penalidade de excesso de dias aplicada a "
            f"{len(max_dias_constraint.excessos)} professores (peso {PESO_EXCESSO_DIAS})."
        )

    if usar_objetivo:
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

    # Excessos de dias (modo flexível)
    if max_dias_constraint and max_dias_constraint.flexivel:
        max_dias_constraint.log_excessos(solver)

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

    # Dias realmente usados por professor (depende do grid)
    if ativa("DIAG_DIAS_USADOS"):
        diagnosticar_dias_usados(base, grid, solver, reuniao_vars)

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