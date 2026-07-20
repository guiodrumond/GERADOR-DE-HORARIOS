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
        self.reuniao_vars = {} # Usado pelo GridBuilder
        self.mapa_professores = {}

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
        self.mapa_professores = self._criar_mapa_professores()

        # Agrupa os slots disponíveis por dia da semana
        dias_slots = {}
        for slot in self.base.slots:
            if slot.dia not in dias_slots:
                dias_slots[slot.dia] = set()
            dias_slots[slot.dia].add(slot.aula)

        for plan in self.base.planejamentos:
            profs_envolvidos = set(self.matcher.filtrar_professores(plan))
            if not profs_envolvidos: 
                continue

            self.reuniao_vars[plan.nome] = {}
            tamanho = plan.tamanho
            
            window_vars = []
            slot_to_windows = {f"{slot.dia}_{slot.aula}": [] for slot in self.base.slots}

            # Cria as Janelas Contínuas válidas para este planejamento no mesmo dia
            for dia, aulas in dias_slots.items():
                sorted_aulas = sorted(list(aulas))
                for i in range(len(sorted_aulas) - tamanho + 1):
                    janela_aulas = sorted_aulas[i : i + tamanho]
                    
                    # Garante que as aulas são estritamente consecutivas
                    if janela_aulas == list(range(janela_aulas[0], janela_aulas[0] + tamanho)):
                        inicio_aula = janela_aulas[0]
                        w_var = self.model.NewBoolVar(f"plan_{plan.nome}_{dia}_aulas_{inicio_aula}_to_{janela_aulas[-1]}")
                        window_vars.append(w_var)
                        
                        # Associa essa janela contínua aos slots que ela cobre
                        for a in janela_aulas:
                            s_id = f"{dia}_{a}"
                            if s_id in slot_to_windows:
                                slot_to_windows[s_id].append(w_var)

            if not window_vars:
                continue

            # 1. Duração/Continuidade: Exatamente UMA janela contínua deve ser escolhida para a reunião
            self.model.Add(sum(window_vars) == 1)

            # 2. Conecta as janelas aos slots individuais para consulta do GridBuilder e restrições de conflito
            for slot in self.base.slots:
                slot_id = f"{slot.dia}_{slot.aula}"
                covering_windows = slot_to_windows.get(slot_id, [])
                
                slot_active_var = self.model.NewBoolVar(f"plan_active_{plan.nome}_{slot_id}")
                self.reuniao_vars[plan.nome][slot_id] = slot_active_var

                if covering_windows:
                    self.model.Add(slot_active_var == sum(covering_windows))
                else:
                    self.model.Add(slot_active_var == 0)

            # 3. Conflito: O Solver não pode alocar aulas reais para os professores envolvidos nos slots da reunião
            for slot in self.base.slots:
                slot_id = f"{slot.dia}_{slot.aula}"
                slot_active_var = self.reuniao_vars[plan.nome][slot_id]
                
                aulas_dos_professores = []
                for bloco in self.base.blocos:
                    profs_bloco = self._professores_do_bloco(bloco)
                    if not profs_bloco.isdisjoint(profs_envolvidos):
                        variaveis_do_bloco = self.variables.get(bloco.id, {})
                        for slot_inicio_id, var_bloco in variaveis_do_bloco.items():
                            if self._bloco_ocupa_slot(bloco, slot_inicio_id, slot_id):
                                auleas_dos_professores_append = aulas_dos_professores.append(var_bloco)
                
                if aulas_dos_professores:
                    self.model.Add(sum(aulas_dos_professores) == 0).OnlyEnforceIf(slot_active_var)

        # 4. Não sobreposição de planejamentos (Coordenadores participam de todos sem conflito de horário)
        for slot in self.base.slots:
            slot_id = f"{slot.dia}_{slot.aula}"
            reunioes_no_slot = []
            
            for plan in self.base.planejamentos:
                if plan.nome in self.reuniao_vars and slot_id in self.reuniao_vars[plan.nome]:
                    reunioes_no_slot.append(self.reuniao_vars[plan.nome][slot_id])
            
            if reunioes_no_slot:
                self.model.Add(sum(reunioes_no_slot) <= 1)