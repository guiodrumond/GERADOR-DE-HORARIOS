import logging

class PedagogicalPairsConstraint:
    def __init__(self, model, variables, base, objective_builder):
        self.model = model
        self.variables = variables
        self.base = base
        self.objective_builder = objective_builder
        self.pares_config = base.pares_pedagogicos

    def build(self):
        # 1. Agrupar turmas espelháveis (mesmo curso e padrao_ftp)
        grupos_espelhamento = self._agrupar_turmas_espelhadas()
        
        # 2. Aplicar o X apenas para turmas que realmente são espelho
        for grupo in grupos_espelhamento:
            if len(grupo) < 2: continue
            
            # Pega as duas primeiras turmas do grupo (ex: 1ADM01 e 1ADM02)
            t1, t2 = grupo[0], grupo[1]
            
            for par in self.pares_config:
                self._forcar_x_sincrono(t1.codigo, t2.codigo, par.especialidade_1, par.especialidade_2)
        return 0

    def _agrupar_turmas_espelhadas(self):
        grupos = {}
        for turma in self.base.turmas:
            # Chave baseada no curso e padrão, para saber quem deve ser espelhado
            chave = f"{turma.curso}_{turma.padrao_ftp}"
            if chave not in grupos: grupos[chave] = []
            grupos[chave].append(turma)
        return list(grupos.values())

    def _forcar_x_sincrono(self, t1_cod, t2_cod, siglaA, siglaB):
        # Localiza os blocos
        bA_t1 = self._get_bloco(t1_cod, siglaA)
        bB_t1 = self._get_bloco(t1_cod, siglaB)
        bA_t2 = self._get_bloco(t2_cod, siglaA)
        bB_t2 = self._get_bloco(t2_cod, siglaB)

        if not (bA_t1 and bB_t1 and bA_t2 and bB_t2): return

        # Força a alternância cruzada: 
        # T1 tem A e T2 tem B -> T1 tem B e T2 tem A (no slot seguinte)
        for slot in self.base.slots:
            if slot.aula % 2 == 0: continue
            
            t_id = f"{slot.dia}_{slot.aula}"
            next_id = f"{slot.dia}_{slot.aula + 1}"
            
            vA1 = self.variables[bA_t1.id].get(t_id)
            vB2 = self.variables[bB_t2.id].get(t_id)
            vB1_next = self.variables[bB_t1.id].get(next_id)
            vA2_next = self.variables[bA_t2.id].get(next_id)

            if all(v is not None for v in [vA1, vB2, vB1_next, vA2_next]):
                match = self.model.NewBoolVar(f"X_{t1_cod}_{t2_cod}_{t_id}")
                # A lógica do X: Se começar invertido, tem que terminar invertido
                self.model.AddBoolAnd([vA1, vB2]).OnlyEnforceIf(match)
                self.model.Add(vB1_next == 1).OnlyEnforceIf(match)
                self.model.Add(vA2_next == 1).OnlyEnforceIf(match)
                self.objective_builder.add_term(match, 500000, "X_PEDAGOGICO")

    def _get_bloco(self, turma_cod, sigla):
        for b in self.base.blocos:
            if b.turma == turma_cod and any(sigla.upper() in c.upper() for c in b.componentes):
                return b
        return None