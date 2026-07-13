class SchedulePrinter:

    DIAS = [
        "SEG",
        "TER",
        "QUA",
        "QUI",
        "SEX",
    ]

    AULAS = [
        1, 2, 3, 4, 5, 6
    ]

    @classmethod
    def print_turma(
        cls,
        schedule,
        turma,
    ):

        print()
        print(
            f"===== {turma} ====="
        )
        print()

        cabecalho = (
            "AULA".ljust(8)
        )

        for dia in cls.DIAS:

            cabecalho += (
                dia.ljust(15)
            )

        print(cabecalho)

        for aula in cls.AULAS:

            linha = (
                str(aula)
                .ljust(8)
            )

            for dia in cls.DIAS:

                entry = (
                    schedule.data[turma]
                    .get(
                        (dia, aula)
                    )
                )

                if entry:

                    texto = "/".join(
                        entry.componentes
                    )

                else:

                    texto = "-"

                linha += (
                    texto[:14]
                    .ljust(15)
                )

            print(linha)