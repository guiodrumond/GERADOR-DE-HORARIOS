import logging
from collections import defaultdict

from src.domain.matchers import PlanejamentoMatcher


class PlanningDiagnostics:

    INVALIDOS = {"", "NONE", "NAN", "A DEFINIR"}

    def __init__(self, base):

        self.base = base
        self.matcher = PlanejamentoMatcher(base)

        self.slots = [
            self._norm_slot(f"{s.dia}_{s.aula}")
            for s in base.slots
        ]

        self.total_slots = len(self.slots)

        self.aulas_por_dia = defaultdict(list)

        for s in base.slots:
            self.aulas_por_dia[self._norm(s.dia)].append(int(float(s.aula)))

        self.mapa_professores = self._criar_mapa_professores()
        self.bloqueios = self._carregar_bloqueios()
        self.blocos_por_turma = self._agrupar_blocos_por_turma()

    # ==================================================
    # ANTES DO SOLVER
    # ==================================================

    def log_pre_solver(self):

        planos = list(getattr(self.base, "planejamentos", []) or [])

        logging.info("=" * 60)
        logging.info("🧩 DIAGNÓSTICO PRÉ-SOLVER: PLANEJAMENTOS")
        logging.info("=" * 60)

        if not planos:
            logging.warning("⚠️ Nenhum planejamento carregado em base.planejamentos.")
            return 0

        todos_professores = {
            p
            for profs in self.mapa_professores.values()
            for p in profs
        }

        impossibilidades = 0
        slots_exigidos = 0
        reunioes_validas = []
        reunioes_por_professor = defaultdict(list)

        for plan in planos:

            participantes = self._participantes(plan)
            tamanho = int(float(plan.tamanho))

            logging.info("")
            logging.info(
                "📌 %s | Tamanho: %s slots | Convocados: %s",
                plan.nome,
                tamanho,
                len(participantes),
            )

            if not participantes:
                logging.warning("   ⚠️ Nenhum professor convocado. A reunião será ignorada.")
                continue

            slots_exigidos += tamanho
            reunioes_validas.append((plan.nome, tamanho, participantes))

            for p in participantes:
                reunioes_por_professor[p].append(plan.nome)

            sem_atribuicao = sorted(participantes - todos_professores)

            if sem_atribuicao:
                logging.warning(
                    "   ⚠️ Convocados sem nenhuma atribuição (nome não bate?): %s",
                    ", ".join(sem_atribuicao),
                )

            impossibilidades += self._checar_turmas(participantes, tamanho)

            self._checar_janelas(participantes, tamanho)

        logging.info("")
        logging.info(
            "📊 Slots exigidos por todas as reuniões (sem sobreposição): %s de %s",
            slots_exigidos,
            self.total_slots,
        )

        if slots_exigidos > self.total_slots:
            logging.error("❌ As reuniões não cabem na semana sem sobreposição.")
            impossibilidades += 1

        impossibilidades += self._checar_turmas_combinado(reunioes_validas)

        self._log_professores_multiplos(reunioes_por_professor)

        logging.info("")

        if impossibilidades:
            logging.error(
                "❌ %s impossibilidade(s) detectada(s) no planejamento.",
                impossibilidades,
            )
        else:
            logging.info("✅ Nenhuma impossibilidade óbvia detectada no planejamento.")

        logging.info("=" * 60)

        return impossibilidades

    def _checar_turmas(self, participantes, tamanho):

        impossiveis = []
        apertadas = []

        for turma, blocos in sorted(self.blocos_por_turma.items()):

            ch = sum(b.tamanho for b in blocos)
            folga = max(0, self.total_slots - ch)

            horas_livres = 0
            convocados_turma = set()

            for b in blocos:

                profs = self._professores_do_bloco(b)

                if profs.isdisjoint(participantes):
                    horas_livres += b.tamanho
                else:
                    convocados_turma |= profs & participantes

            capacidade = folga + horas_livres

            if capacidade < tamanho:
                impossiveis.append(
                    (turma, ch, folga, horas_livres, sorted(convocados_turma))
                )
            elif capacidade < tamanho * 2:
                apertadas.append((turma, capacidade))

        for turma, ch, folga, livres, convocados in impossiveis:
            logging.error(
                "   ❌ %s | CH: %s | Folga: %s | Aulas com não convocados: %s "
                "| Não há como manter a turma ocupada durante a reunião.",
                turma,
                ch,
                folga,
                livres,
            )
            logging.error("      ↳ Professores convocados da turma: %s", ", ".join(convocados))

        if apertadas:
            logging.warning(
                "   ⚠️ Turmas com pouca margem: %s",
                ", ".join(f"{t}({c})" for t, c in apertadas),
            )

        if not impossiveis:
            logging.info("   ✅ Todas as turmas conseguem seguir em aula durante a reunião.")

        return len(impossiveis)

    def _checar_turmas_combinado(self, reunioes):

        if len(reunioes) < 2:
            return 0

        logging.info("")
        logging.info("🔗 Verificação combinada (todas as reuniões, sem sobreposição):")

        impossiveis = 0

        for turma, blocos in sorted(self.blocos_por_turma.items()):

            ch = sum(b.tamanho for b in blocos)
            folga = max(0, self.total_slots - ch)

            exigido = 0
            reunioes_afetadas = []

            for nome, tamanho, participantes in reunioes:

                afeta = any(
                    not self._professores_do_bloco(b).isdisjoint(participantes)
                    for b in blocos
                )

                if afeta:
                    exigido += tamanho
                    reunioes_afetadas.append(nome)

            if exigido == 0:
                continue

            disponivel = folga

            for b in blocos:

                profs = self._professores_do_bloco(b)

                if any(
                    profs.isdisjoint(participantes)
                    for _, _, participantes in reunioes
                ):
                    disponivel += b.tamanho

            if disponivel < exigido:
                impossiveis += 1
                logging.error(
                    "   ❌ %s | Slots de reunião a cobrir: %s | Aulas utilizáveis: %s "
                    "| Reuniões: %s",
                    turma,
                    exigido,
                    disponivel,
                    ", ".join(reunioes_afetadas),
                )

        if not impossiveis:
            logging.info("   ✅ Nenhuma turma estoura na combinação das reuniões.")

        return impossiveis

    def _checar_janelas(self, participantes, tamanho):

        resultados = []

        for dia, aulas in self.aulas_por_dia.items():

            aulas = sorted(aulas)

            for inicio in aulas:

                janela = list(range(inicio, inicio + tamanho))

                if not set(janela).issubset(aulas):
                    continue

                slots = {f"{dia}_{a}" for a in janela}

                indisponiveis = sorted(
                    p for p in participantes
                    if self.bloqueios.get(p, set()) & slots
                )

                resultados.append((f"{dia}_{inicio}_{janela[-1]}", indisponiveis))

        resultados.sort(key=lambda r: len(r[1]))

        logging.info("   Janelas com menos convocados indisponíveis:")

        for janela, indisponiveis in resultados[:5]:
            logging.info(
                "      %s | indisponíveis: %s%s",
                janela,
                len(indisponiveis),
                f" ({', '.join(indisponiveis[:6])}...)" if indisponiveis else "",
            )

        if resultados and resultados[0][1]:
            logging.warning(
                "   ⚠️ Não existe janela em que todos os convocados estejam disponíveis."
            )

    def _log_professores_multiplos(self, reunioes_por_professor):

        multiplos = {
            p: r
            for p, r in reunioes_por_professor.items()
            if len(r) > 1
        }

        if not multiplos:
            return

        logging.info("")
        logging.info("👥 Professores convocados para mais de uma reunião: %s", len(multiplos))

        for prof in sorted(multiplos):
            logging.info("   ↳ %s: %s", prof, ", ".join(multiplos[prof]))

    # ==================================================
    # DEPOIS DO SOLVER
    # ==================================================

    def log_pos_solver(self, solver, reuniao_vars):

        planos = {p.nome: p for p in getattr(self.base, "planejamentos", []) or []}

        logging.info("=" * 60)
        logging.info("📅 PLANEJAMENTOS ALOCADOS")
        logging.info("=" * 60)

        todos = {
            p
            for profs in self.mapa_professores.values()
            for p in profs
        }

        com_reuniao = set()

        for nome, slots in reuniao_vars.items():

            ativos = [s for s, v in slots.items() if solver.Value(v) == 1]

            plan = planos.get(nome)
            participantes = self._participantes(plan) if plan else set()
            com_reuniao |= participantes

            logging.info(
                "📌 %s | %s | %s professores",
                nome,
                ", ".join(sorted(ativos)) or "NÃO ALOCADA",
                len(participantes),
            )

            nomes = sorted(participantes)

            for i in range(0, len(nomes), 6):
                logging.info("   ↳ %s", ", ".join(nomes[i:i + 6]))

        sem_reuniao = sorted(todos - com_reuniao)

        if sem_reuniao:
            logging.info("Professores sem nenhuma reunião: %s", len(sem_reuniao))

            for i in range(0, len(sem_reuniao), 6):
                logging.info("   ↳ %s", ", ".join(sem_reuniao[i:i + 6]))

        logging.info("=" * 60)

    # ==================================================
    # APOIO
    # ==================================================

    def _participantes(self, plan):

        return {
            self._norm(p)
            for p in self.matcher.filtrar_professores(plan)
            if self._norm(p) not in self.INVALIDOS
        }

    def _criar_mapa_professores(self):

        mapa = defaultdict(set)

        for a in self.base.atribuicoes:

            prof = self._norm(a.professor)

            if prof in self.INVALIDOS:
                continue

            mapa[(self._norm(a.turma), self._norm(a.especialidade))].add(prof)

        return mapa

    def _professores_do_bloco(self, bloco):

        profs = set()

        componentes = (
            bloco.componentes
            if isinstance(bloco.componentes, (list, tuple, set))
            else [bloco.componentes]
        )

        for comp in componentes:
            profs |= self.mapa_professores.get(
                (self._norm(bloco.turma), self._norm(comp)),
                set(),
            )

        return profs

    def _agrupar_blocos_por_turma(self):

        grupos = defaultdict(list)

        for b in self.base.blocos or []:
            grupos[self._norm(b.turma)].append(b)

        return grupos

    def _carregar_bloqueios(self):

        return {
            self._norm(prof): {self._norm_slot(s) for s in slots}
            for prof, slots in (getattr(self.base, "disponibilidade", {}) or {}).items()
        }

    def _norm(self, valor):

        return "" if valor is None else str(valor).strip().upper()

    def _norm_slot(self, valor):

        partes = self._norm(valor).replace("_", " ").split()

        if len(partes) == 2:

            try:
                return f"{partes[0]}_{int(float(partes[1]))}"
            except ValueError:
                return f"{partes[0]}_{partes[1]}"

        return self._norm(valor)