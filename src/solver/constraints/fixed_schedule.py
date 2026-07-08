from src.domain.database import BaseDados


class FixedScheduleConstraint:
    """
    Aplica restrições fixas vindas da planilha.

    Exemplo de regras na aba RESTRICOES:

        PROJ_DIA = TER
        PROJ_AULA_INICIAL = 1
        PROJ_AULA_FINAL = 4

    Isso significa que todo bloco PROJ deve começar em TER_1.
    Como o bloco PROJ tem tamanho 4, ele ocupará TER_1 até TER_4.
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

        quantidade = 0

        prefixes = self._prefixos_com_dia_fixo()

        for prefixo in prefixes:

            dia = self._valor_restricao(
                f"{prefixo}_DIA"
            )

            aula_inicial = self._valor_restricao(
                f"{prefixo}_AULA_INICIAL"
            )

            aula_final = self._valor_restricao(
                f"{prefixo}_AULA_FINAL"
            )

            if (
                dia is None
                or aula_inicial is None
                or aula_final is None
            ):
                continue

            slot_inicio_id = (
                f"{dia}_{aula_inicial}"
            )

            for bloco in self.base.blocos:

                if prefixo not in bloco.componentes:
                    continue

                self._validar_tamanho_bloco(
                    bloco=bloco,
                    aula_inicial=int(aula_inicial),
                    aula_final=int(aula_final),
                )

                if slot_inicio_id not in self.variables[bloco.id]:

                    raise ValueError(
                        "Slot fixo inválido para bloco "
                        f"{bloco.id}: {slot_inicio_id}"
                    )

                self.model.Add(
                    self.variables[bloco.id][slot_inicio_id] == 1
                )

                quantidade += 1

        return quantidade

    def _prefixos_com_dia_fixo(self):

        prefixos = []

        for restricao in self.base.restricoes:

            if restricao.regra.endswith("_DIA"):

                prefixo = restricao.regra.replace(
                    "_DIA",
                    ""
                )

                prefixos.append(
                    prefixo
                )

        return prefixos

    def _valor_restricao(
        self,
        regra: str,
    ):

        for restricao in self.base.restricoes:

            if restricao.regra == regra:
                return restricao.valor

        return None

    def _validar_tamanho_bloco(
        self,
        bloco,
        aula_inicial: int,
        aula_final: int,
    ):

        tamanho_esperado = (
            aula_final
            - aula_inicial
            + 1
        )

        if bloco.tamanho != tamanho_esperado:

            raise ValueError(
                "Tamanho incompatível para restrição fixa. "
                f"Bloco: {bloco.id}. "
                f"Tamanho do bloco: {bloco.tamanho}. "
                f"Tamanho esperado: {tamanho_esperado}."
            )