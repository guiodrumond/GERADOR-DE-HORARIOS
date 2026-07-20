from src.scheduling.grid_models import Grid
from src.solver.constraints.planejamento_constraint import PlanejamentoMatcher

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

        # 2. Insere os Planejamentos Coletivos na grade dos professores envolvidos
        if self.solver and self.reuniao_vars and self.base:
            matcher = PlanejamentoMatcher(self.base)
            
            for nome_plan, slots_dict in self.reuniao_vars.items():
                plan = next((p for p in self.base.planejamentos if p.nome == nome_plan), None)
                if not plan:
                    continue
                
                profs_envolvidos = matcher.filtrar_professores(plan)
                
                for slot_id, var in slots_dict.items():
                    if self.solver.Value(var) == 1:
                        dia, aula = slot_id.split('_')
                        for prof in profs_envolvidos:
                            try:
                                grid.set(
                                    turma=prof,
                                    dia=dia,
                                    aula=aula,
                                    texto=f"PLAN: {nome_plan}",
                                    bloco_id="PLANEJAMENTO",
                                    professor=prof,
                                )
                            except Exception:
                                pass # Ignora caso a estrutura da grid seja restrita a turmas

        return grid