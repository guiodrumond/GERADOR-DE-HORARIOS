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
                    aula=aula, # Aqui a aula sempre foi Número Inteiro
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
                        
                        logging.info(f"📅 REUNIÃO AGENDADA: '{nome_plan}' marcada na {dia} (Aula {aula}) para {len(profs_envolvidos)} professores.")
                        
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

        return grid