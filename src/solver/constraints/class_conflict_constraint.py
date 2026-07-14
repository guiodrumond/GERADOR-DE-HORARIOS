from src.domain.database import BaseDados
from src.domain.models import (
    BlocoPedagogico,
    Slot,
)


class TurmaConflictConstraint:
    """
    Impede que uma mesma turma tenha dois blocos ocupando
    o mesmo slot de aula.

    Exemplo proibido:

        1ADM01_MAT_A ocupa SEG_1 e SEG_2
        1ADM01_GEO ocupa SEG_2 e SEG_3

    Como ambos ocupam SEG_2, o modelo deve impedir essa combinação.
    """

    def __init__(
        self,
        model,
        variables,
        base: BaseDados,
    ):

        self.model = model
        self.variables = variables
        self.base = base

    def build(self):

        self._validar_base()

        quantidade = 0

        turmas = self._turmas()

        slot_ids = [
            self._slot_id(slot)
            for slot in self.base.slots
        ]

        for turma in turmas:

            blocos_da_turma = (
                self._blocos_da_turma(
                    turma
                )
            )

            for slot_alvo in slot_ids:

                variaveis_que_ocupam = []

                for bloco in blocos_da_turma:

                    variaveis_do_bloco = (
                        self.variables[bloco.id]
                    )

                    for slot_inicio_id, variavel in variaveis_do_bloco.items():

                        if self._bloco_ocupa_slot(
                            bloco=bloco,
                            slot_inicio_id=slot_inicio_id,
                            slot_alvo_id=slot_alvo,
                        ):

                            variaveis_que_ocupam.append(
                                variavel
                            )

                self.model.Add(
                    sum(
                        variaveis_que_ocupam
                    ) <= 1
                )

                quantidade += 1

        return quantidade

    def _validar_base(self):

        if self.base.blocos is None:
            raise ValueError(
                "base.blocos não foi definido."
            )

        if self.base.slots is None:
            raise ValueError(
                "base.slots não foi definido."
            )

    def _turmas(self):
        # MUDANÇA: Agora pegamos as turmas reais cadastradas na base, 
        # para garantir que o Solver trate 1ADM01 e 1ADM02 separadamente
        return sorted({turma.codigo for turma in self.base.turmas})

    def _blocos_da_turma(self, turma: str):
            blocos_da_turma = []
            for bloco in self.base.blocos:
                # MUDANÇA: Separa o nome da turma caso seja um agrupamento (ex: "1ADM01+1ADM02")
                # Assim, o bloco ocupará a grade da 1ADM01 e também da 1ADM02
                turmas_do_bloco = [t.strip() for t in bloco.turma.split('+')]
                
                if turma in turmas_do_bloco:
                    blocos_da_turma.append(bloco)
                    
            return blocos_da_turma

    def _slot_id(
        self,
        slot: Slot,
    ):

        return (
            f"{slot.dia}_"
            f"{slot.aula}"
        )

    def _parse_slot_id(
        self,
        slot_id: str,
    ):

        partes = slot_id.split("_")

        dia = partes[0]
        aula = int(
            partes[1]
        )

        return dia, aula

    def _bloco_ocupa_slot(
        self,
        bloco: BlocoPedagogico,
        slot_inicio_id: str,
        slot_alvo_id: str,
    ):

        dia_inicio, aula_inicio = (
            self._parse_slot_id(
                slot_inicio_id
            )
        )

        dia_alvo, aula_alvo = (
            self._parse_slot_id(
                slot_alvo_id
            )
        )

        if dia_inicio != dia_alvo:
            return False

        aula_final = (
            aula_inicio
            + bloco.tamanho
            - 1
        )

        return (
            aula_inicio
            <= aula_alvo
            <= aula_final
        )