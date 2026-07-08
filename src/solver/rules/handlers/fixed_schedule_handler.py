class FixedScheduleHandler:

    def __init__(
        self,
        model,
        variables,
        base,
        regras_do_alvo,
    ):

        self.model = model
        self.variables = variables
        self.base = base
        self.regras_do_alvo = regras_do_alvo

    def apply(self, regra):

        # Executa apenas uma vez
        if regra.tipo != "DIA":
            return 0

        dia = self._valor("DIA")

        aula_inicial = self._valor(
            "AULA_INICIAL"
        )

        aula_final = self._valor(
            "AULA_FINAL"
        )

        if (
            dia is None
            or aula_inicial is None
            or aula_final is None
        ):
            return 0

        slot_inicio = (
            f"{dia}_{aula_inicial}"
        )

        quantidade = 0

        for bloco in self.base.blocos:

            if regra.alvo not in bloco.componentes:
                continue

            tamanho_esperado = (
                int(aula_final)
                - int(aula_inicial)
                + 1
            )

            if bloco.tamanho != tamanho_esperado:

                raise ValueError(
                    f"Bloco {bloco.id} "
                    f"possui tamanho "
                    f"{bloco.tamanho} "
                    f"mas regra espera "
                    f"{tamanho_esperado}"
                )

            self.model.Add(
                self.variables[
                    bloco.id
                ][slot_inicio] == 1
            )

            quantidade += 1

        return quantidade

    def _valor(
        self,
        tipo,
    ):

        for regra in self.regras_do_alvo:

            if regra.tipo == tipo:

                return regra.valor

        return None