import logging

class TeacherAvailabilityConstraint:
    def __init__(self, model, variables, base):
        self.model = model
        self.variables = variables
        self.base = base

    def build(self):
        if not hasattr(self.base, 'disponibilidade') or not self.base.disponibilidade:
            return

        logging.info("Aplicando restrições de disponibilidade docente (Estratégia de Varredura Total)...")
        
        # 1. Mapeamento rápido: (Turma, Componente) -> Professor
        map_atribuicao = {}
        for atrib in self.base.atribuicoes:
            chave = (str(atrib.turma).strip(), str(atrib.especialidade).strip())
            map_atribuicao[chave] = str(atrib.professor).strip()

        bloqueios_realizados = 0

        # 2. Aplica os bloqueios varrendo a memória real
        for prof_nome, slots_bloqueados in self.base.disponibilidade.items():
            
            # Pega os blocos do professor
            blocos_prof = []
            for b in self.base.blocos:
                comps = b.componentes if isinstance(b.componentes, list) else [b.componentes]
                for comp in comps:
                    chave_busca = (str(b.turma).strip(), str(comp).strip())
                    if map_atribuicao.get(chave_busca) == prof_nome:
                        blocos_prof.append(b)
                        break 
            
            # Se o professor dá aula, entramos no dicionário de variáveis dele
            for b in blocos_prof:
                if b.id not in self.variables:
                    continue
                    
                # Aqui está a mágica: Olhamos CADA slot construído na memória, um por um
                for slot_key, cp_var in self.variables[b.id].items():
                    dia_var = None
                    aula_var = None
                    
                    # Se for um Objeto Slot
                    if hasattr(slot_key, 'dia') and hasattr(slot_key, 'aula'):
                        dia_var = str(slot_key.dia).strip()
                        aula_var = str(slot_key.aula).strip()
                    # Se for uma Tupla (Ex: ('SEG', 1))
                    elif isinstance(slot_key, tuple) and len(slot_key) == 2:
                        dia_var = str(slot_key[0]).strip()
                        aula_var = str(slot_key[1]).strip()
                    # Se for uma String (Ex: "SEG_1")
                    elif isinstance(slot_key, str):
                        partes = slot_key.replace('_', ' ').split()
                        if len(partes) == 2:
                            dia_var = partes[0]
                            aula_var = partes[1]
                    
                    # Se conseguimos extrair um Dia e Aula dessa variável...
                    if dia_var and aula_var:
                        # Montamos do mesmo jeito que está no slots_bloqueados do Excel
                        formato_excel = f"{dia_var}_{aula_var}" 
                        
                        # Se for um horário proibido, TRANCAMOS com 0!
                        if formato_excel in slots_bloqueados:
                            self.model.Add(cp_var == 0)
                            bloqueios_realizados += 1

        # Esse log será a prova de fogo. Se for 0, o formato da sua variável é um alienígena.
        logging.info(f"✅ FINALIZADO: {bloqueios_realizados} restrições matemáticas de indisponibilidade foram injetadas no motor OR-Tools.")