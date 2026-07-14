class CollectivePlanningObjective:

    PESO_PARTICIPACAO = 100

    def __init__(self, model, planning_variables, teacher_availability, objective_builder, base):
        self.model = model
        self.planning_variables = planning_variables
        self.teacher_availability = teacher_availability
        self.objective_builder = objective_builder
        self.base = base

        self.professores_por_area = self._mapear_professores_por_area()

    def build(self):
        total = 0

        # Para cada área existente na escola
        for area, professores in self.professores_por_area.items():
            
            # Segurança: caso haja alguma área mapeada sem variáveis geradas
            if area not in self.planning_variables:
                continue

            janelas_da_area = self.planning_variables[area]["windows"]

            # Para cada janela possível
            for window_id, janela_var in janelas_da_area.items():
                
                # Para cada professor daquela área
                for professor in professores:
                    livre_var = self.teacher_availability[window_id][professor]

                    participa = self.model.NewBoolVar(
                        self._nome_seguro(f"participa_{area}_{window_id}_{professor}")
                    )

                    # A MÁGICA: O professor participa SE a área dele escolheu essa janela E ele estiver livre
                    self.model.AddMinEquality(participa, [janela_var, livre_var])

                    self.objective_builder.add_term(
                        expression=participa,
                        peso=self.PESO_PARTICIPACAO,
                        descricao=f"PRESENCA {area} {window_id} {professor}",
                    )
                    total += 1

        return total

    def _mapear_professores_por_area(self):
        sigla_para_area = {}
        for esp in self.base.especialidades:
            sigla_para_area[esp.sigla] = esp.componente

        mapa = {}
        for atribuicao in self.base.atribuicoes:
            if not atribuicao.professor:
                continue
            
            area = sigla_para_area.get(atribuicao.especialidade)
            if area:
                if area not in mapa:
                    mapa[area] = set()
                mapa[area].add(atribuicao.professor)

        return {area: sorted(list(profs)) for area, profs in mapa.items()}

    def _nome_seguro(self, texto):
        return texto.replace(" ", "_").replace("+", "_").replace("-", "_").replace("/", "_").replace(".", "_").replace(":", "_")