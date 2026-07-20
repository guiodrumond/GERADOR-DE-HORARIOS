import logging
from src.domain.matchers import PlanejamentoMatcher
from ortools.sat.python import cp_model

class PlanejamentoConstraint:
    def __init__(self, model, variables, base, atribuicoes_map):
        self.model = model
        self.variables = variables # {bloco.id: {slot_inicio_id: bool_var}}
        self.base = base
        self.atribuicoes_map = atribuicoes_map
        self.matcher = PlanejamentoMatcher(base)
        self.reuniao_vars = {} # Pertence à classe
        
        # Cache idêntico ao do ProfessorConflictConstraint
        self.mapa_professores = self._criar_mapa_professores()

    def _criar_mapa_professores(self):
        mapa = {}
        for atribuicao in self.base.atribuicoes:
            chave = (atribuicao.turma, atribuicao.especialidade)
            if chave not in mapa:
                mapa[chave] = []
            if atribuicao.professor:
                mapa[chave].append(atribuicao.professor)
        return mapa

    def _professores_do_bloco(self, bloco):
        professores = set()
        for componente in bloco.componentes:
            chave = (bloco.turma, componente)
            lista_professores = self.mapa_professores.get(chave, [])
            for professor in lista_professores:
                prof_str = str(professor).strip().upper()
                if prof_str not in ["NONE", "NAN", "", "A DEFINIR"]:
                    professores.add(professor)
        return professores

    def _parse_slot_id(self, slot_id: str):
        partes = slot_id.split("_")
        return partes[0], int(partes[1])

    def _bloco_ocupa_slot(self, bloco, slot_inicio_id: str, slot_alvo_id: str):
        dia_inicio, aula_inicio = self._parse_slot_id(slot_inicio_id)
        dia_alvo, aula_alvo = self._parse_slot_id(slot_alvo_id)
        
        if dia_inicio != dia_alvo: 
            return False
            
        aula_final = aula_inicio + bloco.tamanho - 1
        return aula_inicio <= aula_alvo <= aula_final

    def build(self):
        for plan in self.base.planejamentos:
            profs_envolvidos = set(self.matcher.filtrar_professores(plan))
            if not profs_envolvidos: continue

            # Prepara o dicionário para guardar as variáveis desta reunião específica
            self.reuniao_vars[plan.nome] = {}
            reuniao_vars_list = []

            # Cria variáveis: reuniao_ativa[slot] = 1 se a reunião ocorrer naquele slot
            for slot in self.base.slots:
                slot_id = f"{slot.dia}_{slot.aula}"
                var = self.model.NewBoolVar(f"plan_{plan.nome}_{slot_id}")
                
                self.reuniao_vars[plan.nome][slot_id] = var
                reuniao_vars_list.append(var)

            # 1. Duração: A soma dos slots escolhidos deve ser igual ao tamanho da reunião
            self.model.Add(sum(reuniao_vars_list) == plan.tamanho)

            # 2. Conflito: O Solver não pode alocar reuniões e blocos reais no mesmo slot
            for slot in self.base.slots:
                slot_id = f"{slot.dia}_{slot.aula}"
                aulas_dos_professores = []

                for bloco in self.base.blocos:
                    profs_bloco = self._professores_do_bloco(bloco)
                    
                    # Se algum professor do bloco pertence aos professores desta reunião
                    if not profs_bloco.isdisjoint(profs_envolvidos):
                        variaveis_do_bloco = self.variables.get(bloco.id, {})
                        
                        # Verifica se a variável do bloco engloba o slot da reunião
                        for slot_inicio_id, var_bloco in variaveis_do_bloco.items():
                            if self._bloco_ocupa_slot(bloco, slot_inicio_id, slot_id):
                                aulas_dos_professores.append(var_bloco)
                
                # Se a reunião for ativada no 'slot_id', a soma de aulas reais para esses profs DEVE ser zero.
                if aulas_dos_professores:
                    self.model.Add(sum(aulas_dos_professores) == 0).OnlyEnforceIf(self.reuniao_vars[plan.nome][slot_id])