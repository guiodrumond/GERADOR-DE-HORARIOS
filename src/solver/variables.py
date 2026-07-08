from ortools.sat.python import cp_model

from src.domain.database import BaseDados
from src.domain.models import (
    BlocoPedagogico,
    Slot,
)


class DecisionVariableBuilder:
    """
    Cria as variáveis de decisão do modelo CP-SAT.

    Nesta sprint, cada variável representa:

        O bloco pedagógico começa neste slot?

    Exemplo:

        x[1ADM01_MAT_A, SEG_1] = 1

    significa que o bloco 1ADM01_MAT_A começa em SEG aula 1.
    """

    def __init__(self, base: BaseDados):

        self.base = base
        self.model = cp_model.CpModel()
        self.variables = {}

    def build(self):

        self._validar_base()

        for bloco in self.base.blocos:

            self.variables[bloco.id] = {}

            slots_validos = self._slots_validos_para_bloco(
                bloco
            )

            for slot in slots_validos:

                slot_id = self._slot_id(
                    slot
                )

                nome_variavel = (
                    "x__"
                    f"{self._nome_seguro(bloco.id)}"
                    "__"
                    f"{slot_id}"
                )

                self.variables[bloco.id][slot_id] = (
                    self.model.NewBoolVar(
                        nome_variavel
                    )
                )

        return self.model, self.variables

    def _validar_base(self):

        if self.base.blocos is None:
            raise ValueError(
                "base.blocos não foi definido."
            )

        if self.base.slots is None:
            raise ValueError(
                "base.slots não foi definido."
            )

        if len(self.base.blocos) == 0:
            raise ValueError(
                "Nenhum bloco pedagógico encontrado."
            )

        if len(self.base.slots) == 0:
            raise ValueError(
                "Nenhum slot encontrado."
            )

    def _slots_validos_para_bloco(
        self,
        bloco: BlocoPedagogico,
    ):

        slots_validos = []

        max_aula_por_dia = (
            self._max_aula_por_dia()
        )

        for slot in self.base.slots:

            aula_final = (
                slot.aula
                + bloco.tamanho
                - 1
            )

            ultima_aula_do_dia = (
                max_aula_por_dia[slot.dia]
            )

            if aula_final <= ultima_aula_do_dia:

                slots_validos.append(
                    slot
                )

        return slots_validos

    def _max_aula_por_dia(self):

        resultado = {}

        for slot in self.base.slots:

            if slot.dia not in resultado:

                resultado[slot.dia] = slot.aula

            else:

                resultado[slot.dia] = max(
                    resultado[slot.dia],
                    slot.aula,
                )

        return resultado

    def _slot_id(
        self,
        slot: Slot,
    ):

        return (
            f"{slot.dia}_"
            f"{slot.aula}"
        )

    def _nome_seguro(
        self,
        valor: str,
    ):

        return (
            valor
            .replace(" ", "_")
            .replace("+", "_")
            .replace("-", "_")
        )