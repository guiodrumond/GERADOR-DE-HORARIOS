class PlanningVariables:

    def __init__(self, model, planning_windows, base):
        self.model = model
        self.planning_windows = planning_windows
        self.base = base
        
        # Extrai da planilha quais áreas existem (LEST, MEST, CNST, etc)
        self.areas = self._extrair_areas()

    def build(self):
        variables = {}

        # ==========================================
        # 1. CRIAÇÃO DAS REUNIÕES POR ÁREA
        # ==========================================
        for area in self.areas:
            window_vars = {}
            for window in self.planning_windows:
                var = self.model.NewBoolVar(f"plan_{area}_{window.id}")
                window_vars[window.id] = var

            variables[area] = {
                "windows": window_vars,
            }

            # RESTRIÇÃO: A área DEVE escolher exatamente 1 janela na semana inteira
            self.model.AddExactlyOne(window_vars.values())

        # ==========================================
        # 2. RESTRIÇÃO: ZERO SOBREPOSIÇÃO
        # ==========================================
        vars_por_slot = {}
        for window in self.planning_windows:
            for slot in window.slots: # Ex: "SEG_1"
                if slot not in vars_por_slot:
                    vars_por_slot[slot] = []
                
                # Coleta as variáveis de TODAS as áreas que usariam esse mesmo slot
                for area in self.areas:
                    vars_por_slot[slot].append(variables[area]["windows"][window.id])

        # O Solver só permite que, no máximo, 1 reunião ocorra naquele slot de tempo
        for slot, lista_de_vars in vars_por_slot.items():
            self.model.AddAtMostOne(lista_de_vars)

        return variables

    def _extrair_areas(self):
        # Lê todas as especialidades e extrai os componentes únicos (as grandes áreas)
        areas = set()
        for esp in self.base.especialidades:
            if esp.componente:
                areas.add(esp.componente)
        return sorted(list(areas))