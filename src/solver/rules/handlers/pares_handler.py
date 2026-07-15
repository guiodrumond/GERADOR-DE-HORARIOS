from src.data.analyzer import PedagogicalPairsAnalyzer

class ParesHandler:
    """
    PARES
    Garante o cumprimento obrigatório dos Pares Pedagógicos:
    1. Regra Inegociável: As duas disciplinas SEMPRE ocorrem coladas no mesmo dia.
    2. Regra Forte: Se forem pares perfeitos, força o "X" simultâneo.
    """

    def __init__(self, model, variables, base, regras_do_alvo):
        self.model = model
        self.variables = variables
        self.base = base
        self.regras_do_alvo = regras_do_alvo
        self.analyzer = PedagogicalPairsAnalyzer(base)

    def apply(self, regra):
        valor = str(regra.valor).strip().upper()
        if valor not in {"S", "SIM", "TRUE", "1", "V", "VERDADEIRO"}:
            return 0

        analise = self.analyzer.analisar()
        restricoes_adicionadas = 0

        for par in self.base.pares_pedagogicos:
            c1 = par.especialidade_1.upper()
            c2 = par.especialidade_2.upper()
            chave_par = f"{c1} & {c2}"
            
            dados = analise.get(chave_par)
            if not dados:
                continue

            # 1. Adjacência e Mesmo Dia para TODOS
            todas_turmas = set()
            for t1, t2, _, _ in dados["perfeitos"]:
                todas_turmas.add(t1)
                todas_turmas.add(t2)
            for t, _, _ in dados["assimetricos"]:
                todas_turmas.add(t)

            for turma in todas_turmas:
                restricoes_adicionadas += self._forcar_adjacencia_matematica(turma, c1, c2)

            # 2. O 'X' para Pares Perfeitos
            for t1, t2, _, _ in dados["perfeitos"]:
                restricoes_adicionadas += self._forcar_x_simultaneo(t1, t2, c1, c2)
                
        return restricoes_adicionadas

    def _forcar_adjacencia_matematica(self, turma, c1, c2):
        blocos_c1 = self._blocos(turma, c1)
        blocos_c2 = self._blocos(turma, c2)

        if not (blocos_c1 and blocos_c2):
            return 0

        restricoes = 0
        dias = sorted(list({slot.dia for slot in self.base.slots}))

        for dia in dias:
            aulas_do_dia = sorted([slot.aula for slot in self.base.slots if slot.dia == dia])
            
            vars_dia_c1 = [self.variables[b.id][f"{dia}_{a}"] for b in blocos_c1 for a in aulas_do_dia if f"{dia}_{a}" in self.variables[b.id]]
            vars_dia_c2 = [self.variables[b.id][f"{dia}_{a}"] for b in blocos_c2 for a in aulas_do_dia if f"{dia}_{a}" in self.variables[b.id]]
            
            if not vars_dia_c1 or not vars_dia_c2:
                continue

            # 1. Devem ocorrer no mesmo dia (se um ocorrer, o outro também tem que ocorrer)
            self.model.Add(sum(vars_dia_c1) == sum(vars_dia_c2))
            restricoes += 1

            # 2. Matemática da Adjacência: A diferença entre as posições das aulas deve ser igual a 1
            # Criamos variáveis inteiras para representar a aula em que a disciplina ocorre
            pos_c1 = self.model.NewIntVar(0, max(aulas_do_dia), f"pos_c1_{turma}_{dia}")
            pos_c2 = self.model.NewIntVar(0, max(aulas_do_dia), f"pos_c2_{turma}_{dia}")
            
            # Variável booleana para indicar se as disciplinas ocorrem neste dia
            ocorre_neste_dia = self.model.NewBoolVar(f"ocorre_{turma}_{dia}")
            self.model.Add(sum(vars_dia_c1) == 1).OnlyEnforceIf(ocorre_neste_dia)
            self.model.Add(sum(vars_dia_c1) == 0).OnlyEnforceIf(ocorre_neste_dia.Not())

            # Vincula a variável de posição (pos_c1) à variável booleana do slot
            for a in aulas_do_dia:
                slot_id = f"{dia}_{a}"
                v_c1 = sum([self.variables[b.id][slot_id] for b in blocos_c1 if slot_id in self.variables[b.id]])
                v_c2 = sum([self.variables[b.id][slot_id] for b in blocos_c2 if slot_id in self.variables[b.id]])
                
                self.model.Add(pos_c1 == a).OnlyEnforceIf(v_c1 == 1)
                self.model.Add(pos_c2 == a).OnlyEnforceIf(v_c2 == 1)

            # Se ocorre neste dia, a diferença absoluta entre pos_c1 e pos_c2 deve ser EXATAMENTE 1
            # pos_c1 - pos_c2 == 1  OU  pos_c2 - pos_c1 == 1
            diff = self.model.NewIntVar(-max(aulas_do_dia), max(aulas_do_dia), f"diff_{turma}_{dia}")
            self.model.Add(diff == pos_c1 - pos_c2)
            
            abs_diff = self.model.NewIntVar(0, max(aulas_do_dia), f"abs_diff_{turma}_{dia}")
            self.model.AddAbsEquality(abs_diff, diff)
            
            self.model.Add(abs_diff == 1).OnlyEnforceIf(ocorre_neste_dia)

            restricoes += 4

        return restricoes

    def _forcar_x_simultaneo(self, t1, t2, c1, c2):
        blocos_t1_c1 = self._blocos(t1, c1)
        blocos_t1_c2 = self._blocos(t1, c2)
        blocos_t2_c1 = self._blocos(t2, c1)
        blocos_t2_c2 = self._blocos(t2, c2)

        if not (blocos_t1_c1 and blocos_t1_c2 and blocos_t2_c1 and blocos_t2_c2):
            return 0

        restricoes = 0

        for slot in self.base.slots:
            slot_id = f"{slot.dia}_{slot.aula}"
            
            vars_t1_c1 = sum([self.variables[b.id][slot_id] for b in blocos_t1_c1 if slot_id in self.variables[b.id]])
            vars_t1_c2 = sum([self.variables[b.id][slot_id] for b in blocos_t1_c2 if slot_id in self.variables[b.id]])
            vars_t2_c1 = sum([self.variables[b.id][slot_id] for b in blocos_t2_c1 if slot_id in self.variables[b.id]])
            vars_t2_c2 = sum([self.variables[b.id][slot_id] for b in blocos_t2_c2 if slot_id in self.variables[b.id]])

            # O "X" Inquebrável
            self.model.Add(vars_t1_c1 == vars_t2_c2)
            self.model.Add(vars_t1_c2 == vars_t2_c1)
            restricoes += 2

        return restricoes

    def _blocos(self, turma, componente):
        return [b for b in self.base.blocos if b.turma == turma and componente in b.componentes]