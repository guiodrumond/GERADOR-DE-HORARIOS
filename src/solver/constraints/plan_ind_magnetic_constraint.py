import logging

class PlanIndMagneticConstraint:
    def __init__(self, model, variables, base, reuniao_vars=None):
        self.model = model
        self.variables = variables  
        self.base = base
        self.reuniao_vars = reuniao_vars or {}
        self.plan_ind_vars = {}  
        self.mapa_professores = self._criar_mapa_professores()

    def _criar_mapa_professores(self):
        mapa = {}
        for atribuicao in self.base.atribuicoes:
            chave = (atribuicao.turma, atribuicao.especialidade)
            if chave not in mapa: mapa[chave] = []
            if atribuicao.professor:
                p_limpo = str(atribuicao.professor).strip().upper()
                if p_limpo not in ["NONE", "NAN", "", "A DEFINIR"]:
                    mapa[chave].append(p_limpo)
        return mapa

    def _professores_do_bloco(self, bloco):
        professores = set()
        for comp in bloco.componentes:
            for p in self.mapa_professores.get((bloco.turma, comp), []):
                professores.add(p)
        return professores

    def build(self):
        logging.info("🧲 Construindo Planejamento Individual (Regra Magnética)...")
        
        # 1. Lê a meta de cada professor
        metas_plan_ind = {}
        for prof in self.base.professores:
            if prof.nome:
                p_nome = str(prof.nome).strip().upper()
                try:
                    meta = int(float(getattr(prof, 'plan_ind', getattr(prof, 'Plan_Ind', 0))))
                    if meta > 0:
                        metas_plan_ind[p_nome] = meta
                except (ValueError, TypeError):
                    pass

        if not metas_plan_ind:
            return

        # 2. Mapeia os Fantasmas (PA/PV/Avulsas) para não colidir
        slots_fantasmas = {p: set() for p in metas_plan_ind.keys()}
        
        if hasattr(self.base, 'atividades_avulsas') and self.base.atividades_avulsas:
            for ativ in self.base.atividades_avulsas:
                p_nome = str(ativ.professor).strip().upper()
                if p_nome in slots_fantasmas:
                    dia = str(ativ.dia).strip().upper()
                    try:
                        for a in range(int(float(ativ.aula_inicial)), int(float(ativ.aula_final)) + 1):
                            slots_fantasmas[p_nome].add(f"{dia}_{a}")
                    except Exception: pass
                        
        projetos = {}
        for rest in self.base.restricoes:
            if rest.regra.startswith("PA_") or rest.regra.startswith("PV_"):
                partes = rest.regra.split("_")
                tipo, ano, prop = partes[0], str(partes[1]), "_".join(partes[2:])
                if ano not in projetos: projetos[ano] = {}
                if tipo not in projetos[ano]: projetos[ano][tipo] = {}
                projetos[ano][tipo][prop] = rest.valor
                
        for prof in self.base.professores:
            p_nome = str(prof.nome).strip().upper()
            if p_nome not in slots_fantasmas: continue
            if not prof.anos_atuacao or str(prof.anos_atuacao).lower().strip() in ["nan", "none", ""]: continue
            anos_prof = [a.strip()[:-2] if a.strip().endswith(".0") else a.strip() for a in str(prof.anos_atuacao).split(",")]
            for ano in anos_prof:
                if ano in projetos:
                    for tipo, props in projetos[ano].items():
                        dia = str(props.get("DIA", "")).strip().upper()
                        try:
                            for a in range(int(float(props.get("AULA_INICIAL"))), int(float(props.get("AULA_FINAL"))) + 1):
                                slots_fantasmas[p_nome].add(f"{dia}_{a}")
                        except Exception: pass

        # 3. Mapeia Aulas Normais e Reuniões para não colidir
        prof_aula_vars = {p: {} for p in metas_plan_ind.keys()}
        for bloco in self.base.blocos:
            for p in self._professores_do_bloco(bloco):
                if p in prof_aula_vars:
                    for slot_id, var_bloco in self.variables.get(bloco.id, {}).items():
                        prof_aula_vars[p].setdefault(slot_id, []).append(var_bloco)

        prof_reuniao_vars = {p: {} for p in metas_plan_ind.keys()}
        try:
            from src.domain.matchers import PlanejamentoMatcher
            matcher = PlanejamentoMatcher(self.base)
            for nome_plan, slots_dict in self.reuniao_vars.items():
                plan = next((pl for pl in self.base.planejamentos if pl.nome == nome_plan), None)
                if not plan: continue
                profs_env = set(str(pr).strip().upper() for pr in matcher.filtrar_professores(plan))
                for p in prof_reuniao_vars.keys():
                    if p in profs_env:
                        for slot_id, var_plan in slots_dict.items():
                            prof_reuniao_vars[p].setdefault(slot_id, []).append(var_plan)
        except ImportError:
            pass

        slots_ordenados = sorted(self.base.slots, key=lambda s: (s.dia, int(s.aula) if str(s.aula).isdigit() else s.aula))
        slots_por_dia = {}
        for slot in slots_ordenados:
            slots_por_dia.setdefault(slot.dia, []).append(slot)

        # ==========================================
        # 4. CRIAÇÃO DAS VARIÁVEIS E REGRA MAGNÉTICA
        # ==========================================
        for prof, meta in metas_plan_ind.items():
            self.plan_ind_vars[prof] = {}
            vars_totais_prof = []
            vars_por_dia = {dia: [] for dia in slots_por_dia.keys()}

            for dia, slots_do_dia in slots_por_dia.items():
                for slot in slots_do_dia:
                    slot_id = f"{slot.dia}_{slot.aula}"
                    var_pi = self.model.NewBoolVar(f"pi_{prof}_{slot_id}")
                    
                    self.plan_ind_vars[prof][slot_id] = var_pi
                    vars_totais_prof.append(var_pi)
                    vars_por_dia[dia].append((slot, var_pi))

                    # ANTI-COLISÃO (Não pode ter aula e planejamento ao mesmo tempo)
                    aulas_no_slot = prof_aula_vars[prof].get(slot_id, [])
                    reunioes_no_slot = prof_reuniao_vars[prof].get(slot_id, [])
                    if aulas_no_slot or reunioes_no_slot:
                        self.model.Add(sum(aulas_no_slot) + sum(reunioes_no_slot) + var_pi <= 1)
                        
                    if slot_id in slots_fantasmas.get(prof, set()):
                        self.model.Add(var_pi == 0)

            # META: Tem que cumprir exatamente a quantidade da planilha
            self.model.Add(sum(vars_totais_prof) == meta)

            # MAGNÉTICA: Obriga a agrupar blocos (se a meta for maior que 1)
            if meta > 1:
                for dia, slots_vars in vars_por_dia.items():
                    n = len(slots_vars)
                    for i in range(n):
                        slot_atual_obj, var_atual = slots_vars[i]
                        aula_atual = int(float(slot_atual_obj.aula))
                        
                        vizinhos = []
                        # Checa se o slot anterior é colado numericamente (ex: aula 2 e aula 1)
                        if i > 0 and int(float(slots_vars[i-1][0].aula)) == aula_atual - 1:
                            vizinhos.append(slots_vars[i-1][1])
                        # Checa se o slot posterior é colado numericamente (ex: aula 2 e aula 3)
                        if i < n - 1 and int(float(slots_vars[i+1][0].aula)) == aula_atual + 1:
                            vizinhos.append(slots_vars[i+1][1])
                        
                        # MATEMÁTICA PURA: Se este slot for 1, a soma dos vizinhos tem que ser >= 1
                        if vizinhos:
                            self.model.Add(var_atual <= sum(vizinhos))
                        else:
                            # Se por acaso for um dia de 1 aula só, não permite colocar planejamento aqui para não ficar isolado
                            self.model.Add(var_atual == 0)