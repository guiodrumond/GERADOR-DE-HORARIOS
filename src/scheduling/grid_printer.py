class GridPrinter:

    DIAS = [
        "SEG",
        "TER",
        "QUA",
        "QUI",
        "SEX",
    ]

    AULAS = [
        1,
        2,
        3,
        4,
        5,
        6,
    ]

    COL_WIDTH = 20

    @classmethod
    def print_turma(
        cls,
        grid,
        turma,
    ):

        print()
        print(
            f"===== HORÁRIO {turma} ====="
        )
        print()

        cls._print_cabecalho()

        for aula in cls.AULAS:

            cls._print_linha(
                grid=grid,
                turma=turma,
                aula=aula,
            )

        print()

        cls._print_resumo(
            grid,
            turma,
        )

    # =====================================
    # CABEÇALHO
    # =====================================

    @classmethod
    def _print_cabecalho(cls):

        linha = (
            "AULA".ljust(8)
        )

        for dia in cls.DIAS:

            linha += (
                dia.ljust(
                    cls.COL_WIDTH
                )
            )

        print(linha)

        print(
            "-" * len(linha)
        )

    # =====================================
    # LINHA
    # =====================================

    @classmethod
    def _print_linha(
        cls,
        grid,
        turma,
        aula,
    ):

        linha = (
            str(aula)
            .ljust(8)
        )

        for dia in cls.DIAS:

            texto = cls._cell_text(
                grid,
                turma,
                dia,
                aula,
            )

            linha += texto.ljust(
                cls.COL_WIDTH
            )

        print(linha)

    # =====================================
    # TEXTO DA CÉLULA
    # =====================================

    @classmethod
    def _cell_text(
        cls,
        grid,
        turma,
        dia,
        aula,
    ):

        cell = grid.get(
            turma,
            dia,
            aula,
        )

        if cell is None:

            return "-"

        texto = cell.texto

        professor = getattr(
            cell,
            "professor",
            None,
        )

        if professor:

            texto = (
                f"{texto}"
                f"({professor})"
            )

        return texto[
            : cls.COL_WIDTH - 1
        ]

    # =====================================
    # RESUMO
    # =====================================

    @classmethod
    def _print_resumo(
        cls,
        grid,
        turma,
    ):

        total = 0

        componentes = {}

        professores = set()

        for dia in cls.DIAS:

            for aula in cls.AULAS:

                cell = grid.get(
                    turma,
                    dia,
                    aula,
                )

                if cell is None:
                    continue

                total += 1

                componente = (
                    cell.texto
                )

                componentes[
                    componente
                ] = (
                    componentes.get(
                        componente,
                        0,
                    )
                    + 1
                )

                professor = getattr(
                    cell,
                    "professor",
                    None,
                )

                if professor:

                    professores.add(
                        professor
                    )

        print(
            f"Aulas ocupadas: {total}"
        )

        print(
            f"Componentes: {len(componentes)}"
        )

        print(
            f"Professores: {len(professores)}"
        )