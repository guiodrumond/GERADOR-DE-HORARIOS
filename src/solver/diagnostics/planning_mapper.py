import logging
from collections import defaultdict

from ortools.sat.python import cp_model

from src.domain.matchers import PlanejamentoMatcher


class PlanningMapper:

    INVALIDOS = {"", "NONE", "NAN", "A DEFINIR"}

    def __init__(self, base):

        self.base = base
        self.matcher = PlanejamentoMatcher(base)

        self.aulas_por_dia = defaultdict(list)

        for s in base.slots:
            self.aulas_por_dia[self._norm(s.dia)].append(int(float(s.aula)))

        for dia in self.aulas_por_dia:
            self.aulas_por_dia[dia].sort()

        self.dias = list(self.aulas_por_dia.keys())

        self.bloqueios = {
            self._norm(p): {self._norm_slot(s) for s in slots}
            for p, slots in (getattr(base, "disponibilidade", {}) or {}).items()
        }

        self.mapa_professores = self._criar_mapa_professores()
        self.fixos = self._slots_fixos_por_professor()
        self.avulsas = self._slots_avulsas_por_professor()

        self.planos = []

    # ==================================================
    # EXECUÇÃO
    # ==================================================

    def run(self):

        logging.info("=" * 70)
        logging.info("🗺️ PRÉ-MAPEAMENTO DAS REUNIÕES DE PLANEJAMENTO")
        logging.info("=" * 70)

        self.planos = self._montar_planos()

        if not self.planos:
            logging.warning("⚠️ Nenhuma reunião com convocados.")
            return True

        self._log_janelas()
        self._log_mapa_grupos()

        viavel = self._mini_solver(self.planos)

        if viavel:
            logging.info("")
            logging.info("✅ As reuniões cabem sozinhas na semana.")
            logging.info("   O aperto vem da combinação com aulas, Max_Dias e projetos.")
        else:
            logging.error("")
            logging.error("❌ As reuniões NÃO cabem nem sozinhas. Procurando o gargalo...")
            self._isolar_gargalo()

        logging.info("=" * 70)

        return viavel

    # ==================================================
    # PLANOS E JANELAS
    # ==================================================

    def _montar_planos(self):

        planos = []

        for plan in getattr(self.base, "planejamentos", []) or []:

            participantes = {
                self._norm(p)
                for p in self.matcher.filtrar_professores(plan)
                if self._norm(p) not in self.INVALIDOS
            }

            if not participantes:
                continue

            tamanho = int(float(plan.tamanho))
            viaveis = {}
            bloqueadas = {}

            for janela, slots in self._janelas(tamanho):

                motivos = self._motivos_bloqueio(participantes, slots)

                if motivos:
                    bloqueadas[janela] = motivos
                else:
                    viaveis[janela] = slots

            planos.append({
                "nome": plan.nome,
                "grupo": self._norm(getattr(plan, "grupo", None)) or f"_{plan.nome}",
                "participantes": participantes,
                "viaveis": viaveis,
                "bloqueadas": bloqueadas,
            })

        return planos

    def _janelas(self, tamanho):

        for dia in self.dias:

            aulas = self.aulas_por_dia[dia]

            for inicio in aulas:

                janela = list(range(inicio, inicio + tamanho))

                if set(janela).issubset(aulas):
                    yield (
                        f"{dia}_{janela[0]}-{janela[-1]}",
                        [f"{dia}_{a}" for a in janela],
                    )

    def _motivos_bloqueio(self, participantes, slots):

        motivos = []
        slots = set(slots)

        for p in sorted(participantes):

            if self.bloqueios.get(p, set()) & slots:
                motivos.append(f"{p} (indisponível)")

            if self.fixos.get(p, set()) & slots:
                motivos.append(f"{p} (aula fixa)")

            if self.avulsas.get(p, set()) & slots:
                motivos.append(f"{p} (atividade avulsa)")

        return motivos

    # ==================================================
    # LOGS
    # ==================================================

    def _log_janelas(self):

        logging.info("")
        logging.info("📋 JANELAS POSSÍVEIS POR REUNIÃO")

        for p in sorted(self.planos, key=lambda x: len(x["viaveis"])):

            total = len(p["viaveis"]) + len(p["bloqueadas"])

            nivel = (
                logging.error if not p["viaveis"]
                else logging.warning if len(p["viaveis"]) <= 3
                else logging.info
            )

            nivel(
                "   %s | Grupo: %s | Convocados: %s | Janelas viáveis: %s de %s",
                p["nome"],
                p["grupo"],
                len(p["participantes"]),
                len(p["viaveis"]),
                total,
            )

            if len(p["viaveis"]) <= 5:
                nivel("      ✅ %s", ", ".join(p["viaveis"]) or "NENHUMA")

            if len(p["viaveis"]) <= 3:

                contagem = defaultdict(int)

                for motivos in p["bloqueadas"].values():
                    for m in motivos:
                        contagem[m] += 1

                for motivo, qtd in sorted(contagem.items(), key=lambda x: -x[1])[:5]:
                    nivel("      🚫 %s bloqueia %s janela(s)", motivo, qtd)

    def _log_mapa_grupos(self):

        logging.info("")
        logging.info("🧮 DISPUTA DE SLOTS POR GRUPO (reuniões que podem usar cada slot)")

        grupos = defaultdict(list)

        for p in self.planos:
            grupos[p["grupo"]].append(p)

        max_aulas = max(len(a) for a in self.aulas_por_dia.values())

        for grupo, planos in sorted(grupos.items()):

            demanda = sum(len(next(iter(p["viaveis"].values()), [])) or 2 for p in planos)

            logging.info("")
            logging.info(
                "   Grupo %s | Reuniões: %s | Slots exigidos: %s",
                grupo,
                len(planos),
                demanda,
            )

            logging.info("      AULA | " + " | ".join(f"{d:^4}" for d in self.dias))

            for aula in range(1, max_aulas + 1):

                linha = []

                for dia in self.dias:

                    slot = f"{dia}_{aula}"

                    qtd = sum(
                        1 for p in planos
                        if any(slot in s for s in p["viaveis"].values())
                    )

                    linha.append(f"{qtd:^4}")

                logging.info("       %s   | %s", aula, " | ".join(linha))

    # ==================================================
    # MINI-SOLVER
    # ==================================================

    def _mini_solver(self, planos, tempo=20):

        model = cp_model.CpModel()
        uso = defaultdict(lambda: defaultdict(list))

        for p in planos:

            if not p["viaveis"]:
                return False

            vars_janela = []

            for janela, slots in p["viaveis"].items():

                v = model.NewBoolVar(f"{p['nome']}_{janela}")
                vars_janela.append(v)

                for s in slots:
                    uso[p["nome"]][s].append(v)

            model.Add(sum(vars_janela) == 1)

        def ocupa(nome, slot):
            return sum(uso[nome].get(slot, []))

        todos_slots = {s for p in planos for v in p["viaveis"].values() for s in v}

        grupos = defaultdict(list)

        for p in planos:
            grupos[p["grupo"]].append(p["nome"])

        for nomes in grupos.values():
            if len(nomes) > 1:
                for s in todos_slots:
                    model.Add(sum(ocupa(n, s) for n in nomes) <= 1)

        por_prof = defaultdict(list)

        for p in planos:
            for prof in p["participantes"]:
                por_prof[prof].append(p["nome"])

        for nomes in por_prof.values():
            if len(nomes) > 1:
                for s in todos_slots:
                    model.Add(sum(ocupa(n, s) for n in nomes) <= 1)

        solver = cp_model.CpSolver()
        solver.parameters.max_time_in_seconds = tempo
        solver.parameters.num_search_workers = 8

        status = solver.Solve(model)

        return status in (cp_model.OPTIMAL, cp_model.FEASIBLE)

    def _isolar_gargalo(self):

        sem_janela = [p["nome"] for p in self.planos if not p["viaveis"]]

        if sem_janela:
            logging.error("   ❌ Reuniões sem nenhuma janela viável: %s", ", ".join(sem_janela))
            return

        logging.info("   Testando a retirada de cada reunião...")

        culpadas = []

        for p in self.planos:

            restantes = [x for x in self.planos if x["nome"] != p["nome"]]

            if self._mini_solver(restantes, tempo=10):
                culpadas.append(p)

        if culpadas:
            logging.error("   🎯 Retirar qualquer uma destas destrava as reuniões:")

            for p in culpadas:
                logging.error(
                    "      ↳ %s | Grupo: %s | Convocados: %s | Janelas viáveis: %s",
                    p["nome"],
                    p["grupo"],
                    len(p["participantes"]),
                    len(p["viaveis"]),
                )
        else:
            logging.error(
                "   ⚠️ Nenhuma retirada isolada resolve. O conflito envolve várias "
                "reuniões ao mesmo tempo: revise a distribuição dos grupos."
            )

    # ==================================================
    # APOIO
    # ==================================================

    def _criar_mapa_professores(self):

        mapa = defaultdict(set)

        for a in self.base.atribuicoes:

            prof = self._norm(a.professor)

            if prof not in self.INVALIDOS:
                mapa[(self._norm(a.turma), self._norm(a.especialidade))].add(prof)

        return mapa

    def _slots_fixos_por_professor(self):

        regras = defaultdict(dict)

        for r in getattr(self.base, "restricoes", []) or []:

            nome = self._norm(r.regra)

            for tipo in ("AULA_INICIAL", "AULA_FINAL", "DIA"):

                if nome.endswith("_" + tipo):
                    regras[nome[: -len(tipo) - 1]][tipo] = self._norm(r.valor)

        fixos = defaultdict(set)

        for alvo, valores in regras.items():

            if not {"DIA", "AULA_INICIAL", "AULA_FINAL"} <= set(valores):
                continue

            slots = {
                f"{valores['DIA']}_{a}"
                for a in range(
                    int(float(valores["AULA_INICIAL"])),
                    int(float(valores["AULA_FINAL"])) + 1,
                )
            }

            for (turma, esp), profs in self.mapa_professores.items():
                if esp == alvo:
                    for p in profs:
                        fixos[p] |= slots

        return fixos

    def _slots_avulsas_por_professor(self):

        avulsas = defaultdict(set)

        for a in getattr(self.base, "atividades_avulsas", []) or []:

            try:
                ini = int(float(a.aula_inicial))
                fim = int(float(a.aula_final))
            except (TypeError, ValueError):
                continue

            for aula in range(ini, fim + 1):
                avulsas[self._norm(a.professor)].add(f"{self._norm(a.dia)}_{aula}")

        return avulsas

    def _norm(self, valor):

        return "" if valor is None else str(valor).strip().upper()

    def _norm_slot(self, valor):

        partes = self._norm(valor).replace("_", " ").split()

        if len(partes) == 2:
            try:
                return f"{partes[0]}_{int(float(partes[1]))}"
            except ValueError:
                pass

        return self._norm(valor)