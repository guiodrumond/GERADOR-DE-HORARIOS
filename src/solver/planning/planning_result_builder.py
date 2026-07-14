class PlanningResultBuilder:
    def __init__(
        self,
        solver,
        planning_variables,
        planning_windows,
        teacher_availability=None,
    ):
        self.solver = solver
        self.planning_variables = planning_variables
        self.planning_windows = planning_windows
        self.teacher_availability = teacher_availability

    def build(self):
        resultados = []

        # A estrutura agora é um dicionário onde a chave é a Área (ex: "LEST", "MEST")
        for area, data in self.planning_variables.items():
            
            # Procuramos qual das janelas possíveis o Solver ativou (Value == 1)
            for window_id, var in data["windows"].items():
                if self.solver.Value(var):
                    
                    # Encontramos a janela! Agora pegamos os dados dela para o relatório
                    window_obj = next(
                        (w for w in self.planning_windows if w.id == window_id), 
                        None
                    )
                    
                    if window_obj:
                        resultados.append(
                            {
                                "nome": f"PLANEJAMENTO_{area}",
                                "area": area,
                                "dia": window_obj.dia,
                                "aula_inicio": window_obj.aula_inicio,
                                "aula_final": window_obj.aula_final,
                                "window_id": window_id,
                            }
                        )
                        
        return resultados

    @staticmethod
    def print_report(resultados):
        print()
        print("===== RESULTADOS DO PLANEJAMENTO =====")
        
        if not resultados:
            print("Nenhum planejamento foi alocado.")
            return
            
        # Ordena por dia e horário para ficar bonito no terminal
        for r in sorted(resultados, key=lambda x: (x["dia"], x["aula_inicio"])):
            print(
                f"[{r['nome']}] {r['dia']} | Aulas: {r['aula_inicio']} a {r['aula_final']}"
            )