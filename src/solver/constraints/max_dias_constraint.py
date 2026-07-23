import logging

class MaxDiasConstraint:
    def __init__(self, model, variables, base, reuniao_vars=None, plan_ind_vars=None):
        self.model = model
        self.variables = variables
        self.base = base
        self.reuniao_vars = reuniao_vars or {}
        self.plan_ind_vars = plan_ind_vars or {}

    def _clean_slot(self, slot_str):
        try:
            if "_" in str(slot_str):
                d, a = str(slot_str).split("_")
                return f"{d.strip().upper()}_{int(float(a))}"
        except:
            pass
        return str(slot_str).strip().upper()

    def _mapear_fantasmas(self):
        fantasmas = {str(p.nome).strip().upper(): set() for p in self.base.professores if p.nome}
        
        if hasattr(self.base, 'atividades_avulsas'):
            for ativ in self.base.atividades_avulsas:
                p_nome = str(ativ.professor).strip().upper()
                if p_nome in fantasmas:
                    dia = str(ativ.dia).strip().upper()
                    fantasmas[p_nome].add(dia)
                    
        projetos = {}
        for rest in self.base.restricoes:
            if rest.regra.startswith("PA_") or rest.regra.startswith("PV_"):
                partes = rest.regra.split("_")
                ano, prop = str(partes[1]), "_".join(partes[2:])
                if ano not in projetos: projetos[ano] = {}
                projetos[ano][prop] = rest.valor
                
        for prof in self.base.professores:
            p_nome = str(prof.nome).strip().upper()
            if p_nome not in fantasmas or not prof.anos_atuacao: continue
            anos_prof = [a.strip()[:-2] if a.strip().endswith(".0") else a.strip() for a in str(prof.anos_atuacao).split(",")]
            for ano in anos_prof:
                if ano in projetos:
                    dia = str(projetos[ano].get("DIA", "")).strip().upper()
                    if dia: fantasmas[p_nome].add(dia)
        return fantasmas

    def build(self):
        logging.info("⚖️ Construindo Restrição Definitiva de Max Dias (Blindada e Revisada)...")
        fantasmas_por_prof = self._mapear_fantasmas()

        # ==============================================================
        # CORREÇÃO: MAPEIA AS REUNIÕES DE FORMA SEGURA USANDO O MATCHER
        # ==============================================================
        prof_reuniao_vars = {str(p.nome).strip().upper(): [] for p in self.base.professores if p.nome}
        try:
            from src.domain.matchers import PlanejamentoMatcher
            matcher = PlanejamentoMatcher(self.base)
            for nome_plan, slots_dict in self.reuniao_vars.items():
                plan = next((pl for pl in self.base.planejamentos if pl.nome == nome_plan), None)
                if not plan: continue
                profs_env = set(str(pr).strip().upper() for pr in matcher.filtrar_professores(plan))
                
                for p_nome in prof_reuniao_vars.keys():
                    if p_nome in profs_env:
                        for raw_slot, var_plan in slots_dict.items():
                            prof_reuniao_vars[p_nome].append((self._clean_slot(raw_slot), var_plan))
        except Exception as e:
            logging.error(f"Erro ao mapear planejamento coletivo no Max Dias: {e}")

        for prof in self.base.professores:
            if not prof.nome: continue
            p_nome = str(prof.nome).strip().upper()
            
            try:
                max_dias = int(float(prof.max_dias))
            except:
                continue

            if max_dias >= 5: continue

            dias_trabalhados = []
            
            for dia in ["SEG", "TER", "QUA", "QUI", "SEX"]:
                atividades_neste_dia = []
                
                # 1. Aulas Normais
                for bloco in self.base.blocos:
                    match = False
                    if hasattr(bloco, 'professor') and str(bloco.professor).strip().upper() == p_nome:
                        match = True
                    else:
                        for atr in self.base.atribuicoes:
                            if str(atr.turma) == str(bloco.turma) and atr.professor and str(atr.professor).strip().upper() == p_nome:
                                esp_prof = str(atr.especialidade).strip().upper()
                                if esp_prof in str(bloco.id).upper() or any(comp.strip().upper() == esp_prof or comp.strip().upper() in esp_prof or esp_prof in comp.strip().upper() for comp in getattr(bloco, 'componentes', [])):
                                    match = True
                                    break
                    if match:
                        for slot_id, var_bloco in self.variables.get(bloco.id, {}).items():
                            c_id = self._clean_slot(slot_id)
                            if c_id.startswith(dia):
                                atividades_neste_dia.append(var_bloco)

                # 2. Planejamento Coletivo (Agora puxado pela chave corrigida!)
                for slot_id, var_plan in prof_reuniao_vars.get(p_nome, []):
                    if slot_id.startswith(dia):
                        atividades_neste_dia.append(var_plan)
                        
                # 3. Planejamento Individual
                for slot_id, var_pi in self.plan_ind_vars.get(p_nome, {}).items():
                    c_id = self._clean_slot(slot_id)
                    if c_id.startswith(dia):
                        atividades_neste_dia.append(var_pi)

                # 4. Avalia e Trava o dia
                if dia in fantasmas_por_prof.get(p_nome, set()):
                    dias_trabalhados.append(1)
                elif atividades_neste_dia:
                    dia_ativo = self.model.NewBoolVar(f"dia_ativo_{p_nome}_{dia}")
                    self.model.AddMaxEquality(dia_ativo, atividades_neste_dia)
                    dias_trabalhados.append(dia_ativo)

            if dias_trabalhados:
                self.model.Add(sum(dias_trabalhados) <= max_dias)
                logging.info(f"   👤 Prof: {p_nome} | Max Dias: {max_dias} | Juiz aplicou a trava total (Com Plan Coletivo atrelado!).")