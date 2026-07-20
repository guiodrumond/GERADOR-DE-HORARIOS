from src.domain.matchers import PlanejamentoMatcher
from ortools.sat.python import cp_model

class PlanejamentoConstraint:
    def __init__(self, model, variables, base, atribuicoes_map):
        self.model = model
        self.variables = variables # Variáveis de aula {turma: {slot: bool_var}}
        self.base = base
        self.atribuicoes_map = atribuicoes_map # {(turma, esp): prof}
        self.matcher = PlanejamentoMatcher(base)
        self.reuniao_vars = {} # <--- CORREÇÃO: Agora pertence à classe inteira

    def build(self):
        for plan in self.base.planejamentos:
            profs_envolvidos = self.matcher.filtrar_professores(plan)
            if not profs_envolvidos: continue

            # Prepara o dicionário para guardar as variáveis desta reunião específica
            self.reuniao_vars[plan.nome] = {}
            reuniao_vars_list = []

            # Cria variáveis: reuniao_ativa[slot] = 1 se a reunião ocorrer naquele slot
            for slot in self.base.slots:
                slot_id = f"{slot.dia}_{slot.aula}"
                var = self.model.NewBoolVar(f"plan_{plan.nome}_{slot_id}")
                
                # Salva a variável no dicionário da classe e na lista auxiliar
                self.reuniao_vars[plan.nome][slot_id] = var
                reuniao_vars_list.append(var)

            # 1. Duração: A soma dos slots escolhidos deve ser igual ao tamanho da reunião
            self.model.Add(sum(reuniao_vars_list) == plan.tamanho)

            # 2. Conflito: Se a reunião ocorre no slot X, nenhum dos professores pode ter aula no slot X
            for slot in self.base.slots:
                slot_id = f"{slot.dia}_{slot.aula}"
                
                # Coleta todas as variáveis de aula de TODOS os professores da reunião
                aulas_dos_professores = []
                for t in self.base.turmas:
                    for atr in self.base.atribuicoes:
                        if atr.turma == t.codigo and atr.professor in profs_envolvidos:
                            if slot_id in self.variables.get(t.codigo, {}):
                                aulas_dos_professores.append(self.variables[t.codigo][slot_id])
                
                # Se a reunião acontece (1), a soma das aulas desses professores deve ser 0
                if aulas_dos_professores:
                    self.model.Add(sum(aulas_dos_professores) == 0).OnlyEnforceIf(self.reuniao_vars[plan.nome][slot_id])