import logging
from src.scheduling.grid_models import Grid
from src.domain.matchers import PlanejamentoMatcher

class GridBuilder:
    def __init__(self, schedule, solver=None, base=None, reuniao_vars=None):
        self.schedule = schedule
        self.solver = solver
        self.base = base
        self.reuniao_vars = reuniao_vars

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

        # 3. Insere Projetos (PA e PV) automáticos na visualização
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

            logging.info(f"📋 Dicionário de Projetos Extraído: {projetos}")

            for prof in self.base.professores:
                val_anos = str(prof.anos_atuacao).lower().strip()
                if not prof.anos_atuacao or val_anos in ["nan", "none", ""]: 
                    continue
                
                # Limpa os anos de atuação (ex: "3.0" -> "3")
                anos_prof = []
                for a in str(prof.anos_atuacao).split(","):
                    a_clean = a.strip()
                    if a_clean.endswith(".0"):
                        a_clean = a_clean[:-2]
                    anos_prof.append(a_clean)
                
                for ano in anos_prof:
                    if ano in projetos:
                        logging.info(f"👨‍🏫 Professor: {prof.nome} | Ano atuação: {ano} | Projetos Alvo: {list(projetos[ano].keys())}")
                        
                        for tipo, props in projetos[ano].items():
                            dia = props.get("DIA")
                            aula_ini = props.get("AULA_INICIAL")
                            aula_fim = props.get("AULA_FINAL")
                            
                            if dia and aula_ini is not None and aula_fim is not None:
                                dia = str(dia).strip()
                                for aula in range(int(float(aula_ini)), int(float(aula_fim)) + 1):
                                    turma_chave = f"PROJ_{tipo}_{ano}_{prof.nome.replace(' ', '_')}"
                                    
                                    # Verifica se já tem aula/reunião
                                    slot_ocupado_prof = False
                                    for t in grid.turmas():
                                        cel = grid.get(t, dia, aula)
                                        if cel and cel.professor == prof.nome:
                                            slot_ocupado_prof = True
                                            break
                                            
                                    if not slot_ocupado_prof:
                                        logging.info(f"  ✅ INJETANDO {tipo} para {prof.nome} -> {dia}, Aula {aula}")
                                        grid.set(
                                            turma=turma_chave, 
                                            dia=dia, 
                                            aula=aula, 
                                            texto=tipo, 
                                            bloco_id="PROJETO", 
                                            professor=prof.nome
                                        )
                                    else:
                                        logging.info(f"  ❌ BLOQUEADO {tipo} para {prof.nome} -> {dia}, Aula {aula} (Slot já ocupado!)")
                            else:
                                logging.warning(f"  ⚠️ ERRO: Faltam dados na restrição para {tipo}_{ano}. Lidos: {props}")
                                
            logging.info("="*50 + "\n")
            
        return grid