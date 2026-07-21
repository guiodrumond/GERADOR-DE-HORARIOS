import logging

class MaxDiasConstraint:
    def __init__(self, model, variables, base, reuniao_vars=None):
        self.model = model
        self.variables = variables  # {bloco.id: {slot_id: bool_var}}
        self.base = base
        self.reuniao_vars = reuniao_vars or {} # Agora recebe o dicionário real de planejamentos!
        self.mapa_professores = self._criar_mapa_professores()
        self.matcher = None
        try:
            from src.domain.matchers import PlanejamentoMatcher
            self.matcher = PlanejamentoMatcher(base)
        except ImportError:
            pass

    def _criar_mapa_professores(self):
        mapa = {}
        for atribuicao in self.base.atribuicoes:
            chave = (atribuicao.turma, atribuicao.especialidade)
            if chave not in mapa:
                mapa[chave] = []
            if atribuicao.professor:
                p_limpo = str(atribuicao.professor).strip().upper()
                if p_limpo not in ["NONE", "NAN", "", "A DEFINIR"]:
                    mapa[chave].append(p_limpo)
        return mapa

    def _professores_do_bloco(self, bloco):
        professores = set()
        for componente in bloco.componentes:
            chave = (bloco.turma, componente)
            for p in self.mapa_professores.get(chave, []):
                professores.add(p)
        return professores

    def _professor_participa_planejamento(self, prof_nome, plan):
        if not self.matcher:
            return True
        profs_envolvidos = set(str(p).strip().upper() for p in self.matcher.filtrar_professores(plan))
        return prof_nome in profs_envolvidos

    def build(self):
        logging.info("Construindo restrição definitiva de Max Dias (Aulas + Planejamentos reais)...")
        
        limites_dias = {}
        for prof in self.base.professores:
            if prof.nome:
                p_nome = str(prof.nome).strip().upper()
                try:
                    limites_dias[p_nome] = int(float(prof.max_dias))
                except (ValueError, TypeError):
                    limites_dias[p_nome] = 5

        if not limites_dias:
            return

        prof_dias_vars = {}
        for prof in limites_dias.keys():
            prof_dias_vars[prof] = {}
            for slot in self.base.slots:
                dia = str(slot.dia).strip().upper()
                if dia not in prof_dias_vars[prof]:
                    prof_dias_vars[prof][dia] = []

        # 1. Coleta Aulas Normais (Regência)
        for bloco in self.base.blocos:
            profs_bloco = self._professores_do_bloco(bloco)
            for p in profs_bloco:
                if p not in prof_dias_vars:
                    continue
                for slot_inicio_id, var_bloco in self.variables.get(bloco.id, {}).items():
                    dia_inicio = slot_inicio_id.split("_")[0].strip().upper()
                    if dia_inicio in prof_dias_vars[p]:
                        prof_dias_vars[p][dia_inicio].append(var_bloco)

        # 2. Coleta Planejamentos Coletivos (Usando a base real de variáveis da sua restrição)
        for nome_plan, slots_dict in self.reuniao_vars.items():
            plan = next((p for p in self.base.planejamentos if p.nome == nome_plan), None)
            if not plan: continue

            for slot_id, var_plan in slots_dict.items():
                dia_inicio = slot_id.split("_")[0].strip().upper()
                
                for p in prof_dias_vars.keys():
                    if self._professor_participa_planejamento(p, plan):
                        if dia_inicio in prof_dias_vars[p]:
                            prof_dias_vars[p][dia_inicio].append(var_plan)

        # 3. Restrição Final
        dias_disponiveis = sorted(list({str(s.dia).strip().upper() for s in self.base.slots}))

        for prof, max_permitido in limites_dias.items():
            dias_trabalhados_booleans = []

            for dia in dias_disponiveis:
                vars_do_dia = prof_dias_vars.get(prof, {}).get(dia, [])
                if not vars_do_dia:
                    continue

                trab_no_dia = self.model.NewBoolVar(f"trab_{prof}_{dia}")
                soma_ativ_dia = sum(vars_do_dia)
                max_possivel = len(vars_do_dia)
                
                self.model.Add(soma_ativ_dia <= trab_no_dia * max_possivel)
                self.model.Add(soma_ativ_dia >= trab_no_dia)

                dias_trabalhados_booleans.append(trab_no_dia)

            if dias_trabalhados_booleans:
                self.model.Add(sum(dias_trabalhados_booleans) <= max_permitido)
                logging.info(f"👤 Prof: {prof:<20} | Max Dias: {max_permitido} | Restrição injetada.")