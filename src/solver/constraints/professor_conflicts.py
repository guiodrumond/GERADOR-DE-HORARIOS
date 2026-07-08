from src.domain.database import BaseDados
from src.domain.models import (
    BlocoPedagogico,
    Slot,
)


class ProfessorConflictConstraint:
    """
    Impede que um mesmo professor esteja alocado em dois blocos
    que ocupem o mesmo slot real de aula.

    A regra usa a aba ATRIBUICOES:

        Turma + Especialidade -> Professor

    Exemplo:
        1ADM01 | FIS | PROF FIS 1

    Se dois blocos diferentes usam o mesmo professor e ocupam
    o mesmo horário, o modelo deve impedir essa combinação.
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

        self.mapa_professores = (
            self._criar_mapa_professores()
        )

    def build(self):

        self._validar_base()

        quantidade = 0

        professores = self._professores_usados()

        slot_ids = [
            self._slot_id(slot)
            for slot in self.base.slots
        ]

        for professor in professores:

            for slot_alvo in slot_ids:

                variaveis_que_ocupam = (
                    self._variaveis_do_professor_no_slot(
                        professor=professor,
                        slot_alvo_id=slot_alvo,
                    )
                )

                if not variaveis_que_ocupam:
                    continue

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

        if self.base.atribuicoes is None:
            raise ValueError(
                "base.atribuicoes não foi definido."
            )

    def _criar_mapa_professores(self):

        mapa = {}

        for atribuicao in self.base.atribuicoes:

            chave = (
                atribuicao.turma,
                atribuicao.especialidade,
            )

            mapa[chave] = atribuicao.professor

        return mapa

    def _professores_usados(self):

        professores = set()

        for bloco in self.base.blocos:

            for professor in self._professores_do_bloco(
                bloco
            ):

                professores.add(
                    professor
                )

        return sorted(
            professores
        )

    def _professores_do_bloco(
        self,
        bloco: BlocoPedagogico,
    ):

        professores = set()

        for componente in bloco.componentes:

            chave = (
                bloco.turma,
                componente,
            )

            professor = self.mapa_professores.get(
                chave
            )

            if professor:

                professores.add(
                    professor
                )

        return professores

    def _variaveis_do_professor_no_slot(
        self,
        professor: str,
        slot_alvo_id: str,
    ):

        variaveis = {}

        for bloco in self.base.blocos:

            professores_do_bloco = (
                self._professores_do_bloco(
                    bloco
                )
            )

            if professor not in professores_do_bloco:
                continue

            variaveis_do_bloco = (
                self.variables[bloco.id]
            )

            for slot_inicio_id, variavel in variaveis_do_bloco.items():

                if self._bloco_ocupa_slot(
                    bloco=bloco,
                    slot_inicio_id=slot_inicio_id,
                    slot_alvo_id=slot_alvo_id,
                ):

                    chave = (
                        bloco.id,
                        slot_inicio_id,
                    )

                    variaveis[chave] = variavel

        return list(
            variaveis.values()
        )

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