import logging
from collections import defaultdict


class MaxDiasConstraint:

    INVALIDOS = {"", "NONE", "NAN", "A DEFINIR"}

    def __init__(
        self,
        model,
        variables,
        base,
        reuniao_vars=None,
        plan_ind_vars=None,
        flexivel=False,
    ):

        self.model = model
        self.variables = variables
        self.base = base
        self.reuniao_vars = reuniao_vars or {}
        self.plan_ind_vars = plan_ind_vars or {}
        self.flexivel = flexivel

        # prof -> {"var", "max_dias", "dias_vars", "dias_fixos"}
        self.excessos = {}

    # ==================================================
    # APOIO
    # ==================================================

    def _norm(self, valor):

        return "" if valor is None else str(valor).strip().upper()

    def _clean_slot(self, slot_str):

        try:
            if "_" in str(slot_str):
                d, a = str(slot_str).split("_")
                return f"{d.strip().upper()}_{int(float(a))}"
        except Exception:
            pass

        return str(slot_str).strip().upper()

    def _dias(self):

        dias = []

        for slot in self.base.slots:

            dia = self._norm(slot.dia)

            if dia not in dias:
                dias.append(dia)

        return dias

    # ==================================================
    # PA / PV E ATIVIDADES AVULSAS (DIAS FIXOS)
    # ==================================================

    def _mapear_fantasmas(self):

        fantasmas = {
            self._norm(p.nome): set()
            for p in self.base.professores
            if p.nome
        }

        for ativ in getattr(self.base, "atividades_avulsas", []) or []:

            p_nome = self._norm(ativ.professor)

            if p_nome in fantasmas:
                fantasmas[p_nome].add(self._norm(ativ.dia))

        # Chave (ano, tipo): PA e PV do mesmo ano não se sobrescrevem
        projetos = defaultdict(dict)

        for rest in self.base.restricoes:

            regra = self._norm(rest.regra)

            if not (regra.startswith("PA_") or regra.startswith("PV_")):
                continue

            partes = regra.split("_")

            if len(partes) < 3:
                continue

            tipo = partes[0]
            ano = partes[1][:-2] if partes[1].endswith(".0") else partes[1]
            prop = "_".join(partes[2:])

            projetos[(ano, tipo)][prop] = rest.valor

        dias_por_ano = defaultdict(set)

        for (ano, _tipo), props in projetos.items():

            dia = self._norm(props.get("DIA"))

            if dia:
                dias_por_ano[ano].add(dia)

        for prof in self.base.professores:

            p_nome = self._norm(prof.nome)

            if p_nome not in fantasmas or not prof.anos_atuacao:
                continue

            for ano in str(prof.anos_atuacao).split(","):

                ano = ano.strip()
                ano = ano[:-2] if ano.endswith(".0") else ano

                fantasmas[p_nome] |= dias_por_ano.get(ano, set())

        return fantasmas

    # ==================================================
    # MAPAS DE PROFESSORES
    # ==================================================

    def _mapa_professores(self):

        mapa = defaultdict(set)

        for atr in self.base.atribuicoes:

            prof = self._norm(atr.professor)

            if prof in self.INVALIDOS:
                continue

            mapa[(self._norm(atr.turma), self._norm(atr.especialidade))].add(prof)

        return mapa

    def _profs_do_bloco(self, bloco, mapa):

        profs = set()

        prof_direto = self._norm(getattr(bloco, "professor", None))

        if prof_direto and prof_direto not in self.INVALIDOS:
            profs.add(prof_direto)

        componentes = getattr(bloco, "componentes", []) or []

        if not isinstance(componentes, (list, tuple, set)):
            componentes = [componentes]

        for turma in str(bloco.turma).split("+"):
            for comp in componentes:
                profs |= mapa.get((self._norm(turma), self._norm(comp)), set())

        return profs

    def _reunioes_por_prof(self):

        resultado = defaultdict(list)

        if not self.reuniao_vars:
            return resultado

        try:
            from src.domain.matchers import PlanejamentoMatcher

            matcher = PlanejamentoMatcher(self.base)
            planos = {p.nome: p for p in getattr(self.base, "planejamentos", []) or []}

            for nome_plan, slots_dict in self.reuniao_vars.items():

                plan = planos.get(nome_plan)

                if not plan:
                    continue

                convocados = {
                    self._norm(p)
                    for p in matcher.filtrar_professores(plan)
                }

                for p_nome in convocados:
                    for raw_slot, var_plan in slots_dict.items():
                        resultado[p_nome].append((self._clean_slot(raw_slot), var_plan))

        except Exception as e:
            logging.error(f"Erro ao mapear planejamento coletivo no Max Dias: {e}")

        return resultado

    # ==================================================
    # BUILD
    # ==================================================

    def build(self):

        modo = "FLEXÍVEL (penalidade)" if self.flexivel else "RÍGIDO"
        logging.info(f"⚖️ Construindo restrição de Max Dias | Modo: {modo}")

        dias = self._dias()
        fantasmas = self._mapear_fantasmas()
        mapa = self._mapa_professores()
        reunioes = self._reunioes_por_prof()

        blocos_por_prof = defaultdict(list)

        for bloco in self.base.blocos:
            for prof in self._profs_do_bloco(bloco, mapa):
                blocos_por_prof[prof].append(bloco)

        aplicados = 0

        for prof in self.base.professores:

            if not prof.nome:
                continue

            p_nome = self._norm(prof.nome)

            try:
                max_dias = int(float(prof.max_dias))
            except (TypeError, ValueError):
                continue

            if max_dias >= len(dias):
                continue

            atividades_por_dia = defaultdict(list)

            # 1. Aulas
            for bloco in blocos_por_prof.get(p_nome, []):
                for slot_id, var_bloco in self.variables.get(bloco.id, {}).items():
                    dia = self._clean_slot(slot_id).split("_")[0]
                    atividades_por_dia[dia].append(var_bloco)

            # 2. Reuniões (só convocados)
            for slot_id, var_plan in reunioes.get(p_nome, []):
                atividades_por_dia[slot_id.split("_")[0]].append(var_plan)

            # 3. Planejamento individual
            plan_ind = (
                self.plan_ind_vars.get(p_nome)
                or self.plan_ind_vars.get(str(prof.nome).strip())
                or {}
            )

            for slot_id, var_pi in plan_ind.items():
                dia = self._clean_slot(slot_id).split("_")[0]
                atividades_por_dia[dia].append(var_pi)

            # 4. Dias trabalhados
            dias_trabalhados = []
            dias_vars = {}
            dias_fixos = []

            for dia in dias:

                if dia in fantasmas.get(p_nome, set()):
                    dias_trabalhados.append(1)
                    dias_fixos.append(dia)
                    continue

                ativ = atividades_por_dia.get(dia)

                if ativ:
                    dia_ativo = self.model.NewBoolVar(f"dia_ativo_{p_nome}_{dia}")
                    self.model.AddMaxEquality(dia_ativo, ativ)
                    dias_trabalhados.append(dia_ativo)
                    dias_vars[dia] = dia_ativo

            if not dias_trabalhados:
                continue

            if self.flexivel:

                excesso = self.model.NewIntVar(0, len(dias), f"excesso_dias_{p_nome}")
                self.model.Add(sum(dias_trabalhados) - max_dias <= excesso)

                self.excessos[p_nome] = {
                    "var": excesso,
                    "max_dias": max_dias,
                    "dias_vars": dias_vars,
                    "dias_fixos": dias_fixos,
                }

            else:

                self.model.Add(sum(dias_trabalhados) <= max_dias)

            aplicados += 1

            logging.debug(
                f"   👤 {p_nome} | Max Dias: {max_dias} | Dias fixos (PA/PV): {dias_fixos}"
            )

        logging.info(f"   Professores com limite de dias aplicado: {aplicados}")

        return aplicados

    # ==================================================
    # RELATÓRIO (MODO FLEXÍVEL)
    # ==================================================

    def log_excessos(self, solver):

        logging.info("=" * 60)
        logging.info("⚖️ EXCESSO DE DIAS (Max Dias flexível)")
        logging.info("=" * 60)

        total = 0

        for p_nome, info in sorted(self.excessos.items()):

            valor = solver.Value(info["var"])

            if valor <= 0:
                continue

            total += 1

            usados = sorted(
                set(info["dias_fixos"])
                | {d for d, v in info["dias_vars"].items() if solver.Value(v)}
            )

            logging.warning(
                f"   ⚠️ {p_nome} | Max Dias: {info['max_dias']} | Usados: {len(usados)} {usados} "
                f"| Excesso: {valor} | Fixos (PA/PV): {info['dias_fixos']}"
            )

        if total:
            logging.warning(f"   Professores acima do limite: {total} de {len(self.excessos)}")
        else:
            logging.info("   ✅ Todos os professores dentro do Max Dias.")

        logging.info("=" * 60)

        return total