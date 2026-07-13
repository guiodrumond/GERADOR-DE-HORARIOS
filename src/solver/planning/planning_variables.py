class PlanningVariables:

    COLETIVOS = [
        "PLANEJAMENTO_COLETIVO_1",
        "PLANEJAMENTO_COLETIVO_2",
        "PLANEJAMENTO_COLETIVO_3",
    ]

    def __init__(
        self,
        model,
        planning_windows,
    ):

        self.model = model
        self.planning_windows = (
            planning_windows
        )

    def build(self):

        variables = {}

        for coletivo in self.COLETIVOS:

            variables[
                coletivo
            ] = {}

            janela_vars = []

            for window in self.planning_windows:

                var = self.model.NewBoolVar(
                    f"{coletivo}_{window.id}"
                )

                variables[
                    coletivo
                ][
                    window.id
                ] = var

                janela_vars.append(
                    var
                )

            self.model.Add(
                sum(janela_vars) == 1
            )

        return variables