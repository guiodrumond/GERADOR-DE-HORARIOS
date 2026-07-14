class CollectivePlanningObjective:

    COLETIVOS = [
        "PLANEJAMENTO_COLETIVO_1",
        "PLANEJAMENTO_COLETIVO_2",
        "PLANEJAMENTO_COLETIVO_3",
    ]

    PESO_COBERTURA_PROFESSOR = 100

    PESO_PARTICIPACAO = {
        "PLANEJAMENTO_COLETIVO_1": 6,
        "PLANEJAMENTO_COLETIVO_2": 3,
        "PLANEJAMENTO_COLETIVO_3": 1,
    }

    PENALIDADE_ATIVACAO = {
        "PLANEJAMENTO_COLETIVO_1": 0,
        "PLANEJAMENTO_COLETIVO_2": 40,
        "PLANEJAMENTO_COLETIVO_3": 200,
    }

    def __init__(
        self,
        model,
        planning_variables,
        teacher_availability,
        objective_builder,
    ):

        self.model = model
        self.planning_variables = planning_variables
        self.teacher_availability = teacher_availability
        self.objective_builder = objective_builder

        self.participation_vars = {}

    def build(self):

        total = 0

        professores = self._professores()

        for coletivo in self.COLETIVOS:

            total += self._criar_participacoes(
                coletivo=coletivo,
                professores=professores,
            )

        total += self._criar_cobertura_docente(
            professores=professores,
        )

        total += self._penalizar_reunioes_extras()

        return total

    def _criar_participacoes(
        self,
        coletivo,
        professores,
    ):

        total = 0

        self.participation_vars[
            coletivo
        ] = {}

        for window_id, janela_var in self.planning_variables[
            coletivo
        ][
            "windows"
        ].items():

            self.participation_vars[
                coletivo
            ][
                window_id
            ] = {}

            for professor in professores:

                livre_var = self.teacher_availability[
                    window_id
                ][
                    professor
                ]

                participa = self.model.NewBoolVar(
                    self._nome_seguro(
                        f"participa_{coletivo}_{window_id}_{professor}"
                    )
                )

                self.model.Add(
                    participa <= janela_var
                )

                self.model.Add(
                    participa <= livre_var
                )

                self.model.Add(
                    participa >= janela_var + livre_var - 1
                )

                self.participation_vars[
                    coletivo
                ][
                    window_id
                ][
                    professor
                ] = participa

                self.objective_builder.add_term(
                    expression=participa,
                    peso=self.PESO_PARTICIPACAO[
                        coletivo
                    ],
                    descricao=(
                        f"{coletivo} {window_id} {professor}"
                    ),
                )

                total += 1

        return total

    def _criar_cobertura_docente(
        self,
        professores,
    ):

        total = 0

        for professor in professores:

            participacoes = []

            for coletivo in self.COLETIVOS:

                for window_id in self.participation_vars[
                    coletivo
                ]:

                    participa = self.participation_vars[
                        coletivo
                    ][
                        window_id
                    ][
                        professor
                    ]

                    participacoes.append(
                        participa
                    )

            coberto = self.model.NewBoolVar(
                self._nome_seguro(
                    f"professor_coberto_{professor}"
                )
            )

            self.model.AddMaxEquality(
                coberto,
                participacoes,
            )

            self.objective_builder.add_term(
                expression=coberto,
                peso=self.PESO_COBERTURA_PROFESSOR,
                descricao=(
                    f"COBERTURA {professor}"
                ),
            )

            total += 1

        return total

    def _penalizar_reunioes_extras(self):

        total = 0

        for coletivo in self.COLETIVOS:

            active = self.planning_variables[
                coletivo
            ][
                "active"
            ]

            penalidade = self.PENALIDADE_ATIVACAO[
                coletivo
            ]

            if penalidade == 0:
                continue

            self.objective_builder.add_term(
                expression=active,
                peso=-penalidade,
                descricao=(
                    f"PENALIDADE {coletivo}"
                ),
            )

            total += 1

        return total

    def _professores(self):

        primeira_janela = next(
            iter(
                self.teacher_availability
            )
        )

        return sorted(
            self.teacher_availability[
                primeira_janela
            ].keys()
        )

    def _nome_seguro(
        self,
        texto,
    ):

        return (
            texto
            .replace(" ", "_")
            .replace("+", "_")
            .replace("-", "_")
            .replace("/", "_")
            .replace(".", "_")
            .replace(":", "_")
            .replace("(", "_")
            .replace(")", "_")
        )