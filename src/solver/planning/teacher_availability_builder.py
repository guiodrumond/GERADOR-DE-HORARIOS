class TeacherAvailabilityBuilder:

    def __init__(
        self,
        model,
        variables,
        base,
        planning_windows,
    ):

        self.model = model
        self.variables = variables
        self.base = base
        self.planning_windows = planning_windows

        self.professor_por_turma_componente = (
            self._criar_mapa_professores()
        )

    def build(self):

        resultado = {}

        professores = self._professores()

        for window in self.planning_windows:

            resultado[window.id] = {}

            for professor in professores:

                livre = self._criar_variavel_livre(
                    professor=professor,
                    window=window,
                )

                resultado[window.id][professor] = livre

        return resultado

    def _criar_variavel_livre(
        self,
        professor,
        window,
    ):

        ocupacoes = self._ocupacoes_professor_na_janela(
            professor=professor,
            window=window,
        )

        livre = self.model.NewBoolVar(
            self._nome_seguro(
                f"livre_{professor}_{window.id}"
            )
        )

        if not ocupacoes:

            self.model.Add(
                livre == 1
            )

            return livre

        self.model.Add(
            sum(ocupacoes) == 0
        ).OnlyEnforceIf(
            livre
        )

        self.model.Add(
            sum(ocupacoes) >= 1
        ).OnlyEnforceIf(
            livre.Not()
        )

        return livre

    def _ocupacoes_professor_na_janela(
        self,
        professor,
        window,
    ):

        ocupacoes = {}
        slots_janela = set(window.slots)

        for bloco in self.base.blocos:

            for slot_inicio_id, var in self.variables[
                bloco.id
            ].items():

                slot_dia, aula_inicio = self._parse_slot_id(
                    slot_inicio_id
                )

                if slot_dia != window.dia:
                    continue

                componentes_ocupados = (
                    self._componentes_ocupados_por_slot(
                        bloco=bloco,
                        dia=slot_dia,
                        aula_inicio=aula_inicio,
                    )
                )

                for slot_id, componente in componentes_ocupados:

                    if slot_id not in slots_janela:
                        continue

                    professor_componente = (
                        self._professor_do_componente(
                            turma=bloco.turma,
                            componente=componente,
                        )
                    )

                    if professor_componente != professor:
                        continue

                    chave = (
                        bloco.id,
                        slot_inicio_id,
                    )

                    ocupacoes[chave] = var

        return list(
            ocupacoes.values()
        )

    def _componentes_ocupados_por_slot(
        self,
        bloco,
        dia,
        aula_inicio,
    ):

        resultado = []

        if len(bloco.componentes) == 1:

            componente = bloco.componentes[0]

            for offset in range(
                bloco.tamanho
            ):

                aula = (
                    aula_inicio
                    + offset
                )

                resultado.append(
                    (
                        f"{dia}_{aula}",
                        componente,
                    )
                )

            return resultado

        for offset, componente in enumerate(
            bloco.componentes
        ):

            aula = (
                aula_inicio
                + offset
            )

            resultado.append(
                (
                    f"{dia}_{aula}",
                    componente,
                )
            )

        return resultado

    def _criar_mapa_professores(self):

        mapa = {}

        for atribuicao in self.base.atribuicoes:

            chave = (
                atribuicao.turma,
                atribuicao.especialidade,
            )

            mapa[chave] = atribuicao.professor

        return mapa

    def _professor_do_componente(
        self,
        turma,
        componente,
    ):

        return self.professor_por_turma_componente.get(
            (
                turma,
                componente,
            )
        )

    def _professores(self):

        professores = set()

        for atribuicao in self.base.atribuicoes:

            if atribuicao.professor:

                professores.add(
                    atribuicao.professor
                )

        return sorted(
            professores
        )

    def _parse_slot_id(
        self,
        slot_id,
    ):

        dia, aula = slot_id.split(
            "_"
        )

        return (
            dia,
            int(aula),
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
        )