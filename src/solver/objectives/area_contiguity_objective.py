class AreaContiguityObjective:
    PESO_CONTIGUIDADE = 50

    def __init__(self, model, variables, base, objective_builder):
        self.model = model
        self.variables = variables
        self.base = base
        self.objective_builder = objective_builder
        
        self.componente_para_area = self._criar_mapa_componente_area()

    def build(self):
        total_termos = 0
        
        # Mapeia quais variáveis de bloco ocupam qual (turma, dia, aula, area)
        ocupacao = self._mapear_ocupacoes()

        # Avaliar transições para cada turma e dia
        for turma, dias in ocupacao.items():
            for dia, aulas in dias.items():
                
                # Ordena as aulas para garantir que estamos olhando a sequência correta (1, 2, 3...)
                aulas_ordenadas = sorted(aulas.keys())
                
                for i in range(len(aulas_ordenadas) - 1):
                    aula_atual = aulas_ordenadas[i]
                    aula_prox = aulas_ordenadas[i + 1]

                    # Só avalia se as aulas são realmente contíguas (ex: aula 1 e aula 2)
                    if aula_prox != aula_atual + 1:
                        continue

                    # Para cada área que aparece na aula atual
                    for area, vars_atual in aulas[aula_atual].items():
                        
                        # Se a mesma área também tiver chance de aparecer na aula seguinte
                        vars_prox = aulas[aula_prox].get(area, [])
                        
                        if not vars_atual or not vars_prox:
                            continue

                        # area_ativa_atual = 1 se a área ocupar a aula atual
                        area_ativa_atual = self.model.NewBoolVar(f"area_{turma}_{dia}_{aula_atual}_{area}")
                        self.model.Add(area_ativa_atual == sum(vars_atual))

                        # area_ativa_prox = 1 se a MESMA área ocupar a aula seguinte
                        area_ativa_prox = self.model.NewBoolVar(f"area_{turma}_{dia}_{aula_prox}_{area}")
                        self.model.Add(area_ativa_prox == sum(vars_prox))

                        # transicao_mantida = 1 se ambas as aulas forem da mesma área
                        transicao_mantida = self.model.NewBoolVar(f"trans_{turma}_{dia}_{aula_atual}_{aula_prox}_{area}")
                        self.model.AddMinEquality(transicao_mantida, [area_ativa_atual, area_ativa_prox])

                        # Recompensa o Solver por manter o aluno imerso na mesma área
                        self.objective_builder.add_term(
                            expression=transicao_mantida,
                            peso=self.PESO_CONTIGUIDADE,
                            descricao=f"CONTIGUIDADE_AREA {turma} {dia} {aula_atual}->{aula_prox} {area}"
                        )
                        total_termos += 1

        return total_termos

    def _mapear_ocupacoes(self):
        ocupacao = {}
        
        for bloco in self.base.blocos:
            turma = bloco.turma
            if turma not in ocupacao:
                ocupacao[turma] = {}

            for slot_inicio_id, var in self.variables[bloco.id].items():
                dia_inicio, aula_inicio = slot_inicio_id.split("_")
                aula_inicio = int(aula_inicio)

                if dia_inicio not in ocupacao[turma]:
                    ocupacao[turma][dia_inicio] = {}

                # Replica a lógica de componentes ocupados baseada no tamanho do bloco
                if len(bloco.componentes) == 1:
                    componente = bloco.componentes[0]
                    area = self.componente_para_area.get(componente.upper())
                    
                    if area:
                        for offset in range(bloco.tamanho):
                            aula = aula_inicio + offset
                            self._registrar_ocupacao(ocupacao, turma, dia_inicio, aula, area, var)
                else:
                    for offset, componente in enumerate(bloco.componentes):
                        area = self.componente_para_area.get(componente.upper())
                        if area:
                            aula = aula_inicio + offset
                            self._registrar_ocupacao(ocupacao, turma, dia_inicio, aula, area, var)
                        
        return ocupacao

    def _registrar_ocupacao(self, ocupacao, turma, dia, aula, area, var):
        if aula not in ocupacao[turma][dia]:
            ocupacao[turma][dia][aula] = {}
        if area not in ocupacao[turma][dia][aula]:
            ocupacao[turma][dia][aula][area] = []
            
        ocupacao[turma][dia][aula][area].append(var)

    def _criar_mapa_componente_area(self):
        mapa = {}
        for esp in self.base.especialidades:
            mapa[esp.sigla.upper()] = esp.componente.upper()
        return mapa