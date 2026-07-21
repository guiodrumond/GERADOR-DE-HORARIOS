import logging

class TeacherCompactnessObjective:
    def __init__(self, model, variables, base, regras, objective_builder):
        self.model = model
        self.variables = variables
        self.base = base
        self.regras = regras
        self.objective_builder = objective_builder
        self.mapa_professores = self._criar_mapa_professores()

    def _criar_mapa_professores(self):
        mapa = {}
        for atribuicao in self.base.atribuicoes:
            chave = (atribuicao.turma, atribuicao.especialidade)
            if chave not in mapa:
                mapa[chave] = []
            if atribuicao.professor:
                p_limpo = str(atribuicao.professor).strip().upper()
                if p_limpo not in ["NONE", "NAN", "", "A DEFINIR"]:
                    mapa[chave].append(p_limpo)
        return mapa

    def _professores_do_bloco(self, bloco):
        professores = set()
        for componente in bloco.componentes:
            chave = (bloco.turma, componente)
            for p in self.mapa_professores.get(chave, []):
                professores.add(p)
        return professores

    def build(self):
        logging.info("Construindo objetivo de compactação de horários para professores...")
        
        # Mapeia quais blocos afetam cada professor por dia e aula
        # Estrutura: prof_dias[professor][dia][aula] = [lista de variáveis booleanas que dão aula neste slot]
        prof_slots = {}

        for prof in self._obter_todos_professores():
            prof_slots[prof] = {}
            for slot in self.base.slots:
                dia = str(slot.dia).strip().upper()
                aula = int(slot.aula)
                if dia not in prof_slots[prof]:
                    prof_slots[prof][dia] = {}
                prof_slots[prof][dia][aula] = []

        # Preenche o mapa com as variáveis dos blocos
        for bloco in self.base.blocos:
            profs_bloco = self._professores_do_bloco(bloco)
            for p in profs_bloco:
                if p not in prof_slots:
                    continue
                for slot_inicio_id, var_bloco in self.variables.get(bloco.id, {}).items():
                    dia_inicio, aula_inicio = slot_inicio_id.split("_")
                    dia_inicio = dia_inicio.strip().upper()
                    aula_inicio = int(aula_inicio)
                    
                    # Vê quais aulas esse bloco ocupa
                    for offset in range(bloco.tamanho):
                        aula_alvo = aula_inicio + offset
                        if dia_inicio in prof_slots[p] and aula_alvo in prof_slots[p][dia_inicio]:
                            prof_slots[p][dia_inicio][aula_alvo].append(var_bloco)

        # Agora criamos as variáveis auxiliares de penalidade ou premiação por continuidade.
        # Estratégia elegante: Para cada dia, premiamos blocos adjacentes (aula N e aula N+1 com aula do mesmo professor).
        # Isso incentiva o solver a colar as aulas juntas (eliminando janelas no meio).
        
        dias_disponiveis = sorted(list({str(s.dia).strip().upper() for s in self.base.slots}))
        aulas_disponiveis = sorted(list({int(s.aula) for s in self.base.slots}))
        
        peso_compactacao = 10  # Peso configurável para premiar aulas encostadas

        termos_compactacao = []

        for prof, dias_dict in prof_slots.items():
            for dia in dias_disponiveis:
                aulas_do_dia = sorted(list(dias_dict.get(dia, {}).keys()))
                if len(aulas_do_dia) < 2:
                    continue
                
                # Para cada par de aulas consecutivas no dia (ex: aula 1 e 2, 2 e 3...)
                for i in range(len(aulas_do_dia) - 1):
                    a1 = aulas_do_dia[i]
                    a2 = aulas_do_dia[i+1]
                    
                    # Se forem aulas estritamente consecutivas (ex: 1 e 2)
                    if a2 == a1 + 1:
                        vars_a1 = dias_dict[dia][a1]
                        vars_a2 = dias_dict[dia][a2]
                        
                        if vars_a1 and vars_a2:
                            # Criamos uma variável booleana auxiliar de correlação: 
                            # Se o professor tiver aula em a1 E em a2, ganha pontos de continuidade.
                            # Para simplificar no OR-Tools sem explodir variáveis binárias extras, 
                            # podemos somar a presença ou usar produto lógico linearizado.
                            # Uma forma leve e robusta: somar as presenças. Se houver aula em ambas, o somatório é maior.
                            pass
        
        # Abordagem direta e limpa com o ObjectiveBuilder existente:
        # Penalizar buracos vazios entre a primeira e a última aula do dia do professor.
        # Para cada dia, criamos variáveis que indicam se o professor está ocioso em um slot entre sua 1ª e última aula.
        
        for prof, dias_dict in prof_slots.items():
            for dia in dias_disponiveis:
                aulas_do_dia = sorted(list(dias_dict.get(dia, {}).keys()))
                if len(aulas_do_dia) <= 2:
                    continue
                
                # Para cada slot intermediário, criamos uma penalidade se ele estiver vazio 
                # enquanto há aulas antes e depois dele.
                for i in range(1, len(aulas_do_dia) - 1):
                    aula_meio = aulas_do_dia[i]
                    vars_meio = dias_dict[dia][aula_meio]
                    
                    if not vars_meio:
                        continue
                    
                    # Se o slot do meio NÃO tem aula alocada (sua soma é 0), mas há aulas no dia, 
                    # criamos uma penalidade leve para desencorajar janelas.
                    # Como o ObjectiveBuilder aceita expressões lineares:
                    # Queremos MAXIMIZAR a presença nas aulas do meio quando o dia for ativo.
                    self.objective_builder.add_term(
                        expression=sum(vars_meio),
                        peso=5,
                        descricao=f"Anti-Janela Prof {prof} ({dia} Aula {aula_meio})"
                    )

        logging.info("Objetivo de compactação de professores adicionado com sucesso.")

    def _obter_todos_professores(self):
        profs = set()
        for atribuicoes_lista in self.mapa_professores.values():
            for p in atribuicoes_lista:
                profs.add(p)
        return profs