class MaxConsecutiveHandler:

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

        max_consecutivas = int(
            regra.valor
        )

        tamanho_janela = (
            max_consecutivas
            + 1
        )

        quantidade = 0

        for turma in self._turmas():

            blocos = self._blocos_do_alvo(
                turma=turma,
                alvo=regra.alvo,
            )

            if not blocos:
                continue

            for dia in self._dias():

                aulas_do_dia = self._aulas_do_dia(
                    dia
                )

                if len(aulas_do_dia) < tamanho_janela:
                    continue

                for inicio in range(
                    0,
                    len(aulas_do_dia)
                    - tamanho_janela
                    + 1
                ):

                    janela = aulas_do_dia[
                        inicio: inicio + tamanho_janela
                    ]

                    termos = []

                    for bloco in blocos:

                        for slot_inicio_id, variavel in self.variables[
                            bloco.id
                        ].items():

                            coeficiente = (
                                self._quantidade_ocupada_na_janela(
                                    bloco=bloco,
                                    slot_inicio_id=slot_inicio_id,
                                    dia=dia,
                                    janela=janela,
                                )
                            )

                            if coeficiente > 0:

                                termos.append(
                                    coeficiente * variavel
                                )

                    if termos:

                        self.model.Add(
                            sum(termos)
                            <= max_consecutivas
                        )

                        quantidade += 1

        return quantidade

    def _turmas(self):

        return sorted(
            {
                bloco.turma
                for bloco in self.base.blocos
            }
        )

    def _dias(self):

        return sorted(
            {
                slot.dia
                for slot in self.base.slots
            }
        )

    def _aulas_do_dia(
        self,
        dia: str,
    ):

        aulas = [
            slot.aula
            for slot in self.base.slots
            if slot.dia == dia
        ]

        return sorted(
            aulas
        )

    def _blocos_do_alvo(
        self,
        turma: str,
        alvo: str,
    ):

        blocos = []

        for bloco in self.base.blocos:

            if bloco.turma != turma:
                continue

            if alvo in bloco.componentes:

                blocos.append(
                    bloco
                )

        return blocos

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

    def _quantidade_ocupada_na_janela(
        self,
        bloco,
        slot_inicio_id: str,
        dia: str,
        janela: list[int],
    ):

        dia_inicio, aula_inicio = (
            self._parse_slot_id(
                slot_inicio_id
            )
        )

        if dia_inicio != dia:
            return 0

        aula_final = (
            aula_inicio
            + bloco.tamanho
            - 1
        )

        ocupadas = 0

        for aula in janela:

            if (
                aula_inicio
                <= aula
                <= aula_final
            ):

                ocupadas += 1

        return ocupadas