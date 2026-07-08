class DifferentDaysHandler:

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

        if regra.valor != "S":
            return 0

        quantidade = 0

        for turma in self._turmas():

            blocos = (
                self._blocos_do_alvo(
                    turma,
                    regra.alvo,
                )
            )

            if len(blocos) < 2:
                continue

            for i in range(len(blocos)):

                for j in range(
                    i + 1,
                    len(blocos)
                ):

                    quantidade += (
                        self._aplicar_par(
                            blocos[i],
                            blocos[j],
                        )
                    )

        return quantidade

    def _turmas(self):

        return sorted(
            {
                bloco.turma
                for bloco in self.base.blocos
            }
        )

    def _blocos_do_alvo(
        self,
        turma,
        alvo,
    ):

        resultado = []

        for bloco in self.base.blocos:

            if bloco.turma != turma:
                continue

            if alvo in bloco.componentes:

                resultado.append(
                    bloco
                )

        return resultado

    def _aplicar_par(
        self,
        bloco_a,
        bloco_b,
    ):

        quantidade = 0

        dias = [
            "SEG",
            "TER",
            "QUA",
            "QUI",
            "SEX",
        ]

        for dia in dias:

            vars_a = []

            vars_b = []

            for slot_id, var in self.variables[
                bloco_a.id
            ].items():

                if slot_id.startswith(
                    f"{dia}_"
                ):

                    vars_a.append(var)

            for slot_id, var in self.variables[
                bloco_b.id
            ].items():

                if slot_id.startswith(
                    f"{dia}_"
                ):

                    vars_b.append(var)

            self.model.Add(
                sum(vars_a)
                +
                sum(vars_b)
                <= 1
            )

            quantidade += 1

        return quantidade