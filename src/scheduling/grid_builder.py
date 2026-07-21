import logging
from src.scheduling.grid_models import Grid
from src.domain.matchers import PlanejamentoMatcher

class GridBuilder:
    def __init__(self, schedule, solver=None, base=None, reuniao_vars=None, variables=None):
        self.schedule = schedule
        self.solver = solver
        self.base = base
        self.reuniao_vars = reuniao_vars
        self.variables = variables or {}

    def build(self):
        grid = Grid()

        # 1. Carrega as aulas normais das turmas
        for turma, agenda in self.schedule.data.items():
            for (dia, aula), entry in agenda.items():
                grid.set(
                    turma=turma,
                    dia=dia,
                    aula=aula, 
                    texto=entry.componente,
                    bloco_id=entry.bloco_id,
                    professor=entry.professor,
                )

        # 2. Insere os Planejamentos Coletivos (Reuniões)
        if self.solver and self.reuniao_vars and self.base:
            matcher = PlanejamentoMatcher(self.base)
            
            for nome_plan, slots_dict in self.reuniao_vars.items():
                plan = next((p for p in self.base.planejamentos if p.nome == nome_plan), None)
                if not plan:
                    continue
                
                profs_envolvidos = matcher.filtrar_professores(plan)
                if not profs_envolvidos:
                    continue
                    
                for slot_id, var in slots_dict.items():
                    if self.solver.Value(var) == 1:
                        dia, aula_str = slot_id.split('_')
                        aula = int(aula_str) 
                        
                        for prof in profs_envolvidos:
                            turma_virtual = f"PLAN_{nome_plan}_{prof.replace(' ', '_')}"
                            try:
                                grid.set(
                                    turma=turma_virtual,
                                    dia=dia,
                                    aula=aula, 
                                    texto=f"{nome_plan}", 
                                    bloco_id="PLANEJAMENTO",
                                    professor=prof,
                                )
                            except Exception as e:
                                logging.error(f"❌ Erro ao injetar {nome_plan} para {prof} no grid: {e}")

        # 3. Insere Projetos (PA e PV) automáticos (PRIORIDADE ALTA)
        if self.base:
            logging.info("\n" + "="*50)
            logging.info("🔍 INICIANDO MAPEAMENTO DE PA/PV VIRTUAIS")
            logging.info("="*50)
            
            projetos = {}
            for rest in self.base.restricoes:
                if rest.regra.startswith("PA_") or rest.regra.startswith("PV_"):
                    partes = rest.regra.split("_")
                    tipo = partes[0]
                    ano = str(partes[1])
                    prop = "_".join(partes[2:])
                    if ano not in projetos: projetos[ano] = {}
                    if tipo not in projetos[ano]: projetos[ano][tipo] = {}
                    projetos[ano][tipo][prop] = rest.valor

            for prof in self.base.professores:
                val_anos = str(prof.anos_atuacao).lower().strip()
                if not prof.anos_atuacao or val_anos in ["nan", "none", ""]: 
                    continue
                
                anos_prof = []
                for a in str(prof.anos_atuacao).split(","):
                    a_clean = a.strip()
                    if a_clean.endswith(".0"):
                        a_clean = a_clean[:-2]
                    anos_prof.append(a_clean)
                
                for ano in anos_prof:
                    if ano in projetos:
                        for tipo, props in projetos[ano].items():
                            dia = props.get("DIA")
                            aula_ini = props.get("AULA_INICIAL")
                            aula_fim = props.get("AULA_FINAL")
                            
                            if dia and aula_ini is not None and aula_fim is not None:
                                dia = str(dia).strip()
                                for aula in range(int(float(aula_ini)), int(float(aula_fim)) + 1):
                                    turma_chave = f"PROJ_{tipo}_{ano}_{prof.nome.replace(' ', '_')}"
                                    
                                    slot_ocupado_prof = False
                                    for t in grid.turmas():
                                        cel = grid.get(t, dia, aula)
                                        if cel and cel.professor == prof.nome:
                                            slot_ocupado_prof = True
                                            break
                                            
                                    if not slot_ocupado_prof:
                                        grid.set(
                                            turma=turma_chave, 
                                            dia=dia, 
                                            aula=aula, 
                                            texto=tipo, 
                                            bloco_id="PROJETO", 
                                            professor=prof.nome
                                        )
                            else:
                                logging.warning(f"  ⚠️ ERRO: Faltam dados na restrição para {tipo}_{ano}. Lidos: {props}")
            logging.info("="*50 + "\n")

        # ==========================================================
        # 4. Insere Atividades Avulsas (PRIORIDADE ALTA)
        # ==========================================================
        if hasattr(self.base, 'atividades_avulsas') and self.base.atividades_avulsas:
            logging.info("\n" + "="*50)
            logging.info("🔍 INICIANDO MAPEAMENTO DE ATIVIDADES AVULSAS")
            logging.info("="*50)
            
            for ativ in self.base.atividades_avulsas:
                prof_nome = ativ.professor
                # Tenta pegar o nome da atividade (pode estar como 'atividade' ou 'nome' na sua classe)
                texto_ativ = getattr(ativ, 'atividade', getattr(ativ, 'nome', 'ATIVIDADE'))
                dia = ativ.dia
                
                try:
                    a_ini = int(float(ativ.aula_inicial))
                    a_fim = int(float(ativ.aula_final))
                    
                    for aula in range(a_ini, a_fim + 1):
                        turma_virtual = f"ATIV_{texto_ativ.replace(' ', '_')}_{prof_nome.replace(' ', '_')}"
                        
                        grid.set(
                            turma=turma_virtual,
                            dia=dia,
                            aula=aula,
                            texto=texto_ativ,
                            bloco_id="ATIVIDADE",
                            professor=prof_nome
                        )
                except Exception as e:
                    logging.error(f"❌ Erro ao injetar {texto_ativ} para {prof_nome}: {e}")

        # 4. PREENCHIMENTO RÍGIDO: "A DEFINIR" ATÉ ATINGIR A CH
        if self.base:
            logging.info("\n" + "="*50)
            logging.info("🔍 INICIANDO PREENCHIMENTO 'A DEFINIR' (FATOR CH)")
            logging.info("="*50)
            
            dias_semana = ['SEG', 'TER', 'QUA', 'QUI', 'SEX']
            aulas_possiveis = [1, 2, 3, 4, 5, 6]
            
            for prof in self.base.professores:
                print(f"DEBUG PROFESSOR {prof.nome}: {prof.__dict__}")
                ch_total = int(float(getattr(prof, 'carga_horaria', getattr(prof, 'ch', 0))))
                if ch_total <= 0:
                    continue
                
                indisponiveis = []
                if hasattr(self.base, 'disponibilidade') and self.base.disponibilidade:
                    indisponiveis = self.base.disponibilidade.get(prof.nome, [])

                # Passo A: Mapeia exatamente o que o professor já tem na grade
                aulas_por_dia = {d: [] for d in dias_semana}
                ocupadas = 0
                
                for dia in dias_semana:
                    for aula in aulas_possiveis:
                        ocupado_neste_slot = False
                        for t in grid.turmas():
                            cel = grid.get(t, dia, aula)
                            if cel and cel.professor == prof.nome:
                                ocupado_neste_slot = True
                                break
                        
                        if ocupado_neste_slot:
                            aulas_por_dia[dia].append(aula)
                            ocupadas += 1
                                
                deficit = ch_total - ocupadas
                
                if deficit > 0:
                    logging.info(f"👨‍🏫 {prof.nome}: CH={ch_total}, Alocadas={ocupadas}. Preenchendo {deficit} slots...")
                    
                    # Passo B: Classifica os slots livres por prioridade
                    janelas_sanduiche = []  # Buracos no meio das aulas do dia (Prioridade 1)
                    janelas_borda = []      # Logo antes da primeira ou logo após a última (Prioridade 2)
                    outros_ativos = []      # Outros horários nos dias que ele já vai à escola (Prioridade 3)
                    inativos = []           # Dias em que ele não tem aula nenhuma (Prioridade 4)
                    
                    for dia in dias_semana:
                        aulas_do_dia = aulas_por_dia[dia]
                        
                        for aula in aulas_possiveis:
                            slot_str = f"{dia}_{aula}"
                            
                            # Se já tem aula ou está indisponível, pula
                            if aula in aulas_do_dia or slot_str in indisponiveis:
                                continue
                                
                            if len(aulas_do_dia) > 0:
                                primeira_aula = min(aulas_do_dia)
                                ultima_aula = max(aulas_do_dia)
                                
                                if primeira_aula < aula < ultima_aula:
                                    janelas_sanduiche.append((dia, aula))
                                elif aula == primeira_aula - 1 or aula == ultima_aula + 1:
                                    janelas_borda.append((dia, aula))
                                else:
                                    outros_ativos.append((dia, aula))
                            else:
                                inativos.append((dia, aula))
                    
                    # Concatena a lista de tentativas na ordem correta de prioridade
                    slots_para_preencher = janelas_sanduiche + janelas_borda + outros_ativos + inativos
                    
                    # Passo C: Injeta o "A DEFINIR" consumindo o déficit
                    for dia, aula in slots_para_preencher:
                        if deficit <= 0:
                            break

                        turma_virtual = f"ADEF_{prof.nome.replace(' ', '_')}"    
                        try:
                            grid.set(
                                turma=turma_virtual, # ID único para não sobrescrever ninguém!
                                dia=dia,
                                aula=aula,
                                texto="A DEFINIR",   # Texto real
                                bloco_id="A_DEFINIR",
                                professor=prof.nome
                            )
                            deficit -= 1
                        except Exception as e:
                            logging.error(f"❌ Erro ao injetar A DEFINIR para {prof.nome}: {e}")
                            
                    if deficit > 0:
                        logging.warning(f"  ⚠️ {prof.nome} precisava de mais {deficit} slots, mas faltou espaço físico disponível!")

            logging.info("="*50 + "\n")

        return grid

        return grid