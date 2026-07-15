class AreaCompactnessObjective:
    """
    Sistema de Premiação focado em SEQUÊNCIAS CONTÍNUAS (Janela Deslizante).
    Só pontua se as aulas da mesma área estiverem estritamente coladas umas nas outras,
    suportando corretamente blocos multi-aulas (dobradinhas/quádruplas).
    """

    def __init__(self, model, variables, base, regras, objective_builder):
        self.model = model
        self.variables = variables
        self.base = base
        self.regras = regras
        self.objective_builder = objective_builder
        
        self.AREAS_CONHECIMENTO = {
            "LEST": ["POR", "EDF", "ING", "ART"],
            "CNST": ["FIS", "QUI", "BIO"],
            "CHSA": ["GEO", "FIL", "HIS", "SOC"]
        }

    def build(self):
        turmas = list({b.turma for b in self.base.blocos})
        dias = sorted(list({slot.dia for slot in self.base.slots}))
        
        for turma in turmas:
            for dia in dias:
                aulas_do_dia = sorted([slot.aula for slot in self.base.slots if slot.dia == dia])
                
                for componente_area, siglas in self.AREAS_CONHECIMENTO.items():
                    
                    # 1. Mapeia se aquele SLOT ESPECÍFICO tem uma aula ativa dessa Área
                    slot_is_area = {}
                    for a in aulas_do_dia:
                        vars_no_slot = []
                        for b in self.base.blocos:
                            
                            # === BLINDAGEM CONTRA O EXCEL ===
                            # Garante que 'componentes' seja tratado como lista e ignora espaços em branco invisíveis
                            comps = b.componentes if isinstance(b.componentes, list) else [b.componentes]
                            
                            if b.turma == turma and any(str(sigla).strip().upper() in siglas for sigla in comps):
                                
                                # === RETROVISOR DE DOBRADINHAS / BLOCOS MULTI-AULA ===
                                # Lê o tamanho real do bloco (aulas/tamanho/duração)
                                tamanho = getattr(b, 'aulas', getattr(b, 'tamanho', getattr(b, 'duracao', 1)))
                                
                                # Verifica se o bloco começou na aula atual ou em aulas anteriores e se estende até aqui
                                for i in range(tamanho):
                                    start_aula = a - i
                                    if start_aula > 0:
                                        start_slot_id = f"{dia}_{start_aula}"
                                        if start_slot_id in self.variables[b.id]:
                                            vars_no_slot.append(self.variables[b.id][start_slot_id])
                        
                        # Criamos a variável booleana de presença da área neste slot específico
                        b_is_area = self.model.NewBoolVar(f"is_area_{turma}_{componente_area}_{dia}_{a}")
                        if vars_no_slot:
                            # Se qualquer variável de início mapeada estiver ativa, o slot pertence à Área
                            self.model.Add(sum(vars_no_slot) >= 1).OnlyEnforceIf(b_is_area)
                            self.model.Add(sum(vars_no_slot) == 0).OnlyEnforceIf(b_is_area.Not())
                        else:
                            self.model.Add(b_is_area == 0)
                            
                        slot_is_area[a] = b_is_area

                    # 2. Janelas Deslizantes para Sequências Contínuas
                    
                    # Janelas de tamanho 4 (Mínimo desejável)
                    for i in range(len(aulas_do_dia) - 3):
                        janela = [slot_is_area[aulas_do_dia[j]] for j in range(i, i + 4)]
                        b_win4 = self.model.NewBoolVar(f"win4_{turma}_{componente_area}_{dia}_{i}")
                        self.model.Add(sum(janela) == 4).OnlyEnforceIf(b_win4)
                        self.model.Add(sum(janela) < 4).OnlyEnforceIf(b_win4.Not())
                        self._adicionar_premio(b_win4, 150, f"SEQ CONTINUA 4 [{componente_area}] {turma} {dia} Aulas {aulas_do_dia[i]}-{aulas_do_dia[i+3]}")

                    # Janelas de tamanho 5
                    for i in range(len(aulas_do_dia) - 4):
                        janela = [slot_is_area[aulas_do_dia[j]] for j in range(i, i + 5)]
                        b_win5 = self.model.NewBoolVar(f"win5_{turma}_{componente_area}_{dia}_{i}")
                        self.model.Add(sum(janela) == 5).OnlyEnforceIf(b_win5)
                        self.model.Add(sum(janela) < 5).OnlyEnforceIf(b_win5.Not())
                        self._adicionar_premio(b_win5, 300, f"SEQ CONTINUA 5 [{componente_area}] {turma} {dia} Aulas {aulas_do_dia[i]}-{aulas_do_dia[i+4]}")

                    # Janelas de tamanho 6
                    for i in range(len(aulas_do_dia) - 5):
                        janela = [slot_is_area[aulas_do_dia[j]] for j in range(i, i + 6)]
                        b_win6 = self.model.NewBoolVar(f"win6_{turma}_{componente_area}_{dia}_{i}")
                        self.model.Add(sum(janela) == 6).OnlyEnforceIf(b_win6)
                        self.model.Add(sum(janela) < 6).OnlyEnforceIf(b_win6.Not())
                        self._adicionar_premio(b_win6, 500, f"SEQ CONTINUA 6 [{componente_area}] {turma} {dia} Aulas {aulas_do_dia[i]}-{aulas_do_dia[i+5]}")

    def _adicionar_premio(self, variavel_booleana, pontos, descricao):
        if hasattr(self.objective_builder, 'add_term'):
            self.objective_builder.add_term(variavel_booleana, pontos, descricao)
        elif hasattr(self.objective_builder, 'adicionar_termo'):
            self.objective_builder.adicionar_termo(variavel_booleana, pontos, descricao)
        elif hasattr(self.objective_builder, 'termos'):
            self.objective_builder.termos.append(variavel_booleana * pontos)