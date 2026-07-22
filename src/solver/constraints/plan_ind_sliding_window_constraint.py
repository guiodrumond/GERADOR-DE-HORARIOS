import logging

class PlanIndSlidingWindowConstraint:
    def __init__(self, model, variables, base, reuniao_vars=None):
        self.model = model
        self.variables = variables  
        self.base = base
        self.reuniao_vars = reuniao_vars or {}
        self.plan_ind_vars = {}  
        self.bloco_to_prof = self._mapear_blocos_professores()

    def _clean_slot(self, slot_str):
        try:
            if "_" in str(slot_str):
                d, a = str(slot_str).split("_")
                return f"{d.strip().upper()}_{int(float(a))}"
        except:
            pass
        return str(slot_str).strip().upper()

    def _mapear_blocos_professores(self):
        mapa = {}
        for bloco in self.base.blocos:
            profs_deste_bloco = set()
            
            if hasattr(bloco, 'professor') and bloco.professor:
                p_limpo = str(bloco.professor).strip().upper()
                if p_limpo not in ["NONE", "NAN", "", "A DEFINIR"]:
                    profs_deste_bloco.add(p_limpo)
                    
            if not profs_deste_bloco:
                for atr in self.base.atribuicoes:
                    if str(atr.turma).strip() == str(bloco.turma).strip():
                        esp_prof = str(atr.especialidade).strip().upper()
                        match = False
                        if esp_prof in str(bloco.id).upper():
                            match = True
                        for comp in getattr(bloco, 'componentes', []):
                            comp_str = str(comp).strip().upper()
                            if comp_str == esp_prof or comp_str in esp_prof or esp_prof in comp_str:
                                match = True
                        if match and atr.professor:
                            p_limpo = str(atr.professor).strip().upper()
                            if p_limpo not in ["NONE", "NAN", "", "A DEFINIR"]:
                                profs_deste_bloco.add(p_limpo)
            mapa[bloco.id] = profs_deste_bloco
        return mapa

    def _calcular_tamanhos(self, total):
        if total <= 0: return []
        blocos = []
        rest = total
        if rest % 2 != 0:
            blocos.append(1)
            rest -= 1
        while rest > 0:
            blocos.append(2)
            rest -= 2
        return blocos

    def build(self):
        logging.info("🪟 Construindo Janela Deslizante (Limpeza + Sombra do Bloco Ativadas)...")
        
        metas_plan_ind = {}
        for prof in self.base.professores:
            if prof.nome:
                p_nome = str(prof.nome).strip().upper()
                try:
                    meta = int(float(getattr(prof, 'plan_ind', getattr(prof, 'Plan_Ind', 0))))
                    if meta > 0: metas_plan_ind[p_nome] = meta
                except: pass

        if not metas_plan_ind:
            return

        # 2. Mapeia os Fantasmas
        slots_fantasmas = {p: set() for p in metas_plan_ind.keys()}
        
        if hasattr(self.base, 'atividades_avulsas') and self.base.atividades_avulsas:
            for ativ in self.base.atividades_avulsas:
                p_nome = str(ativ.professor).strip().upper()
                if p_nome in slots_fantasmas:
                    dia = str(ativ.dia).strip().upper()
                    try:
                        for a in range(int(float(ativ.aula_inicial)), int(float(ativ.aula_final)) + 1):
                            slots_fantasmas[p_nome].add(self._clean_slot(f"{dia}_{a}"))
                    except: pass
                        
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
                                slots_fantasmas[p_nome].add(self._clean_slot(f"{dia}_{a}"))
                        except: pass

        # ==============================================================
        # 3. MAPEAMENTO COM PROJEÇÃO DE SOMBRA (O FIM DOS CHOQUES)
        # ==============================================================
        prof_aula_vars = {p: {} for p in metas_plan_ind.keys()}
        
        for bloco in self.base.blocos:
            profs = self.bloco_to_prof.get(bloco.id, set())
            
            # Descobre o tamanho do bloco (Padrão 2 para escolas estaduais)
            tamanho_bloco = 2 
            for attr in ['tamanho', 'aulas', 'duracao', 'qtd_aulas']:
                if hasattr(bloco, attr):
                    try:
                        val = int(float(getattr(bloco, attr)))
                        if val > 0: tamanho_bloco = val
                        break
                    except: pass
                    
            for p in profs:
                if p in prof_aula_vars:
                    for raw_slot_id, var_bloco in self.variables.get(bloco.id, {}).items():
                        c_id = self._clean_slot(raw_slot_id)
                        
                        if "_" in c_id:
                            d, a_str = c_id.split("_")
                            try:
                                a_idx = int(float(a_str))
                                # MAGIA: Projeta a variável para frente ocupando todos os slots do bloco!
                                for offset in range(tamanho_bloco):
                                    target_slot = f"{d}_{a_idx + offset}"
                                    prof_aula_vars[p].setdefault(target_slot, []).append(var_bloco)
                            except:
                                prof_aula_vars[p].setdefault(c_id, []).append(var_bloco)
                        else:
                            prof_aula_vars[p].setdefault(c_id, []).append(var_bloco)

        # Faz o mesmo para as reuniões coletivas
        prof_reuniao_vars = {p: {} for p in metas_plan_ind.keys()}
        try:
            from src.domain.matchers import PlanejamentoMatcher
            matcher = PlanejamentoMatcher(self.base)
            for nome_plan, slots_dict in self.reuniao_vars.items():
                plan = next((pl for pl in self.base.planejamentos if pl.nome == nome_plan), None)
                if not plan: continue
                
                tamanho_plan = 2
                for attr in ['tamanho', 'aulas', 'duracao']:
                    if hasattr(plan, attr):
                        try:
                            val = int(float(getattr(plan, attr)))
                            if val > 0: tamanho_plan = val
                            break
                        except: pass
                
                profs_env = set(str(pr).strip().upper() for pr in matcher.filtrar_professores(plan))
                for p in prof_reuniao_vars.keys():
                    if p in profs_env:
                        for raw_slot_id, var_plan in slots_dict.items():
                            c_id = self._clean_slot(raw_slot_id)
                            if "_" in c_id:
                                d, a_str = c_id.split("_")
                                try:
                                    a_idx = int(float(a_str))
                                    for offset in range(tamanho_plan):
                                        target_slot = f"{d}_{a_idx + offset}"
                                        prof_reuniao_vars[p].setdefault(target_slot, []).append(var_plan)
                                except:
                                    prof_reuniao_vars[p].setdefault(c_id, []).append(var_plan)
        except ImportError:
            pass

        slots_ordenados = sorted(self.base.slots, key=lambda s: (s.dia, int(float(s.aula))))
        slots_por_dia = {}
        for slot in slots_ordenados:
            slots_por_dia.setdefault(slot.dia, []).append(slot)

        # ==========================================
        # 4. A MÁGICA DA JANELA DESLIZANTE
        # ==========================================
        for prof, meta in metas_plan_ind.items():
            self.plan_ind_vars[prof] = {}
            tamanhos_necessarios = self._calcular_tamanhos(meta)
            
            cobertura_por_slot = {self._clean_slot(f"{d}_{s.aula}"): [] for d, slots in slots_por_dia.items() for s in slots}

            for b_idx, tam in enumerate(tamanhos_necessarios):
                opcoes_deste_bloco = []
                
                for dia, slots_do_dia in slots_por_dia.items():
                    n_slots = len(slots_do_dia)
                    for i in range(n_slots - tam + 1):
                        consecutivos = True
                        for k in range(tam - 1):
                            aula_atual = int(float(slots_do_dia[i+k].aula))
                            aula_prox = int(float(slots_do_dia[i+k+1].aula))
                            if aula_prox != aula_atual + 1:
                                consecutivos = False
                                break
                                
                        if not consecutivos:
                            continue
                            
                        w_var = self.model.NewBoolVar(f"w_{prof}_bloco{b_idx}_{dia}_start_{i}")
                        opcoes_deste_bloco.append(w_var)
                        
                        for k in range(tam):
                            c_id = self._clean_slot(f"{dia}_{slots_do_dia[i+k].aula}")
                            cobertura_por_slot[c_id].append(w_var)
                            
                if opcoes_deste_bloco:
                    self.model.AddExactlyOne(opcoes_deste_bloco)
                else:
                    logging.warning(f"⚠️ Impossível criar bloco de tamanho {tam} para {prof}.")

            for dia, slots_do_dia in slots_por_dia.items():
                for slot in slots_do_dia:
                    c_id = self._clean_slot(f"{dia}_{slot.aula}")
                    var_pi = self.model.NewBoolVar(f"pi_{prof}_{c_id}")
                    self.plan_ind_vars[prof][c_id] = var_pi
                    
                    w_vars_que_passam_aqui = cobertura_por_slot[c_id]
                    self.model.Add(var_pi == sum(w_vars_que_passam_aqui))
                    
                    # 🛡️ BLINDAGEM BOOLEANA
                    aulas_no_slot = prof_aula_vars[prof].get(c_id, [])
                    reunioes_no_slot = prof_reuniao_vars[prof].get(c_id, [])
                    
                    for v_aula in aulas_no_slot:
                        self.model.AddImplication(var_pi, v_aula.Not())
                        
                    for v_reuniao in reunioes_no_slot:
                        self.model.AddImplication(var_pi, v_reuniao.Not())
                        
                    # Impede planejamento nos slots fantasmas
                    if c_id in slots_fantasmas.get(prof, set()):
                        self.model.Add(var_pi == 0)