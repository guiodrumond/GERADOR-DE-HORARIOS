from src.data.analyzer import PedagogicalPairsAnalyzer

class PedagogicalPairsConstraint:
    """
    Garante o cumprimento OBRIGATÓRIO (Hard Constraint) dos Pares Pedagógicos.
    Evita o Paradoxo do Espelho identificando assimetrias REAIS nos blocos gerados.
    """

    def __init__(self, model, variables, base, objective_builder=None):
        self.model = model
        self.variables = variables
        self.base = base
        self.analyzer = PedagogicalPairsAnalyzer(base)

    def build(self):
        analise = self.analyzer.analisar()

        # Cache para buscas rápidas
        self.active_t_c_s = {}
        for bloco in self.base.blocos:
            if len(bloco.componentes) == 1:
                comp = bloco.componentes[0].upper()
                turma = bloco.turma
                for slot_id, var in self.variables[bloco.id].items():
                    key = (turma, comp, slot_id)
                    self.active_t_c_s.setdefault(key, []).append(var)

        for par in self.base.pares_pedagogicos:
            c1 = par.especialidade_1.upper()
            c2 = par.especialidade_2.upper()
            chave_par = f"{c1} & {c2}"
            
            dados = analise.get(chave_par)
            if not dados:
                continue
                
            for t1, t2, _, _ in dados["perfeitos"]:
                # DIAGNÓSTICO ABSOLUTO: 
                # Contamos as aulas REAIS de cada turma para ter 100% de certeza se o espelho é possível.
                t1_c1 = self._aulas_reais(t1, c1)
                t1_c2 = self._aulas_reais(t1, c2)
                t2_c1 = self._aulas_reais(t2, c1)
                t2_c2 = self._aulas_reais(t2, c2)

                is_balanced = (t1_c1 == t1_c2) and (t2_c1 == t2_c2) and (t1_c1 == t2_c1) and (t1_c1 > 0)

                if is_balanced:
                    self._forcar_x_simultaneo(t1, t2, c1, c2)
                    self._forcar_adjacencia_restrita(t1, c1, c2)
                    self._forcar_adjacencia_restrita(t2, c1, c2)
                else:
                    self._evitar_simultaneidade_interna(t1, c1, c2)
                    self._evitar_simultaneidade_interna(t2, c1, c2)

            for t, _, _ in dados["assimetricos"]:
                t_c1 = self._aulas_reais(t, c1)
                t_c2 = self._aulas_reais(t, c2)
                is_balanced = (t_c1 == t_c2) and (t_c1 > 0)

                if is_balanced:
                    self._forcar_adjacencia_restrita(t, c1, c2)
                else:
                    self._evitar_simultaneidade_interna(t, c1, c2)

    # ==================================================
    # REGRAS ESTRUTURAIS
    # ==================================================

    def _forcar_adjacencia_restrita(self, turma, c1, c2):
        dias = sorted(list({slot.dia for slot in self.base.slots}))
        for dia in dias:
            aulas_do_dia = sorted([slot.aula for slot in self.base.slots if slot.dia == dia])
            
            for idx, a in enumerate(aulas_do_dia):
                slot_id = f"{dia}_{a}"
                v_c1 = self._get_var(turma, c1, slot_id)
                v_c2 = self._get_var(turma, c2, slot_id)
                
                vizinhos_c1, vizinhos_c2 = [], []
                
                if idx > 0:
                    a_ant = aulas_do_dia[idx - 1]
                    vizinhos_c1.append(self._get_var(turma, c1, f"{dia}_{a_ant}"))
                    vizinhos_c2.append(self._get_var(turma, c2, f"{dia}_{a_ant}"))
                if idx < len(aulas_do_dia) - 1:
                    a_prox = aulas_do_dia[idx + 1]
                    vizinhos_c1.append(self._get_var(turma, c1, f"{dia}_{a_prox}"))
                    vizinhos_c2.append(self._get_var(turma, c2, f"{dia}_{a_prox}"))

                if not isinstance(v_c1, int):
                    b_c1 = self.model.NewBoolVar(f'is_c1_{turma}_{slot_id}')
                    self.model.Add(v_c1 > 0).OnlyEnforceIf(b_c1)
                    self.model.Add(v_c1 == 0).OnlyEnforceIf(b_c1.Not())
                    if vizinhos_c2:
                        self.model.Add(sum(vizinhos_c2) >= 1).OnlyEnforceIf(b_c1)
                    else:
                        self.model.Add(v_c1 == 0)
                        
                if not isinstance(v_c2, int):
                    b_c2 = self.model.NewBoolVar(f'is_c2_{turma}_{slot_id}')
                    self.model.Add(v_c2 > 0).OnlyEnforceIf(b_c2)
                    self.model.Add(v_c2 == 0).OnlyEnforceIf(b_c2.Not())
                    if vizinhos_c1:
                        self.model.Add(sum(vizinhos_c1) >= 1).OnlyEnforceIf(b_c2)
                    else:
                        self.model.Add(v_c2 == 0)

    def _forcar_x_simultaneo(self, t1, t2, c1, c2):
        for slot in self.base.slots:
            slot_id = f"{slot.dia}_{slot.aula}"
            v_t1_c1 = self._get_var(t1, c1, slot_id)
            v_t1_c2 = self._get_var(t1, c2, slot_id)
            v_t2_c1 = self._get_var(t2, c1, slot_id)
            v_t2_c2 = self._get_var(t2, c2, slot_id)

            self.model.Add(v_t1_c1 == v_t2_c2)
            self.model.Add(v_t1_c2 == v_t2_c1)

    def _evitar_simultaneidade_interna(self, turma, c1, c2):
        for slot in self.base.slots:
            slot_id = f"{slot.dia}_{slot.aula}"
            v_c1 = self._get_var(turma, c1, slot_id)
            v_c2 = self._get_var(turma, c2, slot_id)
            if not isinstance(v_c1, int) and not isinstance(v_c2, int):
                self.model.Add(v_c1 + v_c2 <= 1)

    # ==================================================
    # UTILITÁRIOS
    # ==================================================

    def _get_var(self, turma, comp, slot_id):
        vars_list = self.active_t_c_s.get((turma, comp, slot_id), [])
        return sum(vars_list) if vars_list else 0

    def _aulas_reais(self, turma, comp):
        """
        Conta QUANTOS blocos da disciplina a turma realmente possui na memória.
        Isso anula qualquer erro de tipo (string/int) vindo do Excel.
        """
        total = 0
        for bloco in self.base.blocos:
            if bloco.turma == turma and comp in bloco.componentes:
                total += bloco.tamanho
        return total