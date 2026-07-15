from ortools.sat.python import cp_model
from src.domain.database import BaseDados
from src.domain.models import BlocoPedagogico, Slot

class DecisionVariableBuilder:
    """
    Cria as variáveis de decisão do modelo CP-SAT.
    x[bloco.id][slot.id] = 1 significa que o bloco inicia no slot.
    """

    def __init__(self, base: BaseDados):
        self.base = base
        self.model = cp_model.CpModel()
        self.variables = {}

    def build(self):
        self._validar_base()
        # Otimização: Calcula o limite de aulas por dia apenas UMA vez
        max_aula_por_dia = self._max_aula_por_dia()

        for bloco in self.base.blocos:
            self.variables[bloco.id] = {}
            slots_validos = self._slots_validos_para_bloco(bloco, max_aula_por_dia)

            for slot in slots_validos:
                slot_id = self._slot_id(slot)
                nome_variavel = f"x__{self._nome_seguro(bloco.id)}__{slot_id}"
                self.variables[bloco.id][slot_id] = self.model.NewBoolVar(nome_variavel)

        return self.model, self.variables

    def _validar_base(self):
        if not self.base.blocos:
            raise ValueError("base.blocos não foi definido ou está vazio. Execute o Builder primeiro.")
        if not self.base.slots:
            raise ValueError("base.slots não foi definido ou está vazio.")

    def _slots_validos_para_bloco(self, bloco: BlocoPedagogico, max_aula_por_dia: dict):
        slots_validos = []
        for slot in self.base.slots:
            aula_final = slot.aula + bloco.tamanho - 1
            ultima_aula_do_dia = max_aula_por_dia.get(slot.dia, 0)
            
            if aula_final <= ultima_aula_do_dia:
                slots_validos.append(slot)
        return slots_validos

    def _max_aula_por_dia(self):
        resultado = {}
        for slot in self.base.slots:
            resultado[slot.dia] = max(resultado.get(slot.dia, 0), slot.aula)
        return resultado

    def _slot_id(self, slot: Slot):
        return f"{slot.dia}_{slot.aula}"

    def _nome_seguro(self, valor: str):
        return valor.replace(" ", "_").replace("+", "_").replace("-", "_")