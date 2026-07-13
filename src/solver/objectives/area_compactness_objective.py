class AreaCompactnessObjective:
    """
    Premia blocos contínuos de áreas do conhecimento.

    Usa regras:

        CHSA_BLOCO_MINIMO      4
        CHSA_BLOCO_ACEITAVEL   5
        CHSA_BLOCO_OTIMO       6

    Exemplo:
        Se CHSA ocupar 6 aulas consecutivas no mesmo dia,
        recebe bônus maior do que ocupar apenas 4.
    """

    PESOS = {
        "BLOCO_MINIMO": 10,
        "BLOCO_ACEITAVEL": 30,
        "BLOCO_OTIMO": 60,
    }

    TIPOS_SUPORTADOS = {
        "BLOCO_MINIMO",
        "BLOCO_ACEITAVEL",
        "BLOCO_OTIMO",
    }

    def __init__(
        self,
        model,
        variables,
        base,
        regras,
        objective_builder,
    ):

        self.model = model
        self.variables = variables
        self.base = base
        self.regras = regras
        self.objective_builder = objective_builder

        self.componente_para_area = (
            self._criar_mapa_componente_area()
        )

    # ==================================================
    # BUILD
    # ==================================================

    def build(self):

        total = 0

        for regra in self.regras:

            if regra.tipo not in self.TIPOS_SUPORTADOS:
                continue

            total += self._aplicar_regra(
                regra
            )

        return total

    # ==================================================
    # REGRA
    # ==================================================

    def _aplicar_regra(
        self,
        regra,
    ):

        area = regra.alvo

        tamanho_janela = int(
            regra.valor
        )

        peso = self.PESOS[
            regra.tipo
        ]

        total = 0

        for turma in self._turmas():

            for dia in self._dias():

                aulas = self._aulas_do_dia(
                    dia
                )

                for aula_inicio in aulas:

                    aula_final = (
                        aula_inicio
                        + tamanho_janela
                        - 1
                    )

                    if aula_final not in aulas:
                        continue

                    expressao = (
                        self._expressao_area_na_janela(
                            turma=turma,
                            area=area,
                            dia=dia,
                            aula_inicio=aula_inicio,
                            aula_final=aula_final,
                        )
                    )

                    if expressao is None:
                        continue

                    bonus = self.model.NewBoolVar(
                        self._nome_seguro(
                            f"bonus_compact_{turma}_{area}_{dia}_"
                            f"{aula_inicio}_{aula_final}_{regra.tipo}"
                        )
                    )

                    self.model.Add(
                        expressao >= tamanho_janela
                    ).OnlyEnforceIf(
                        bonus
                    )

                    self.model.Add(
                        expressao <= tamanho_janela - 1
                    ).OnlyEnforceIf(
                        bonus.Not()
                    )

                    self.objective_builder.add_term(
                        expression=bonus,
                        peso=peso,
                        descricao=(
                            f"{area} {regra.tipo} "
                            f"{turma} {dia} "
                            f"{aula_inicio}-{aula_final}"
                        ),
                    )

                    total += 1

        return total

    # ==================================================
    # EXPRESSÃO
    # ==================================================

    def _expressao_area_na_janela(
        self,
        turma,
        area,
        dia,
        aula_inicio,
        aula_final,
    ):

        termos = []

        for bloco in self.base.blocos:

            if bloco.turma != turma:
                continue

            if not self._bloco_pertence_area(
                bloco,
                area,
            ):
                continue

            for slot_id, var in self.variables[
                bloco.id
            ].items():

                slot_dia, slot_aula = (
                    self._parse_slot_id(
                        slot_id
                    )
                )

                if slot_dia != dia:
                    continue

                coeficiente = (
                    self._coeficiente_area_na_janela(
                        bloco=bloco,
                        area=area,
                        bloco_inicio=slot_aula,
                        janela_inicio=aula_inicio,
                        janela_final=aula_final,
                    )
                )

                if coeficiente > 0:

                    termos.append(
                        coeficiente * var
                    )

        if not termos:
            return None

        return sum(
            termos
        )

    def _coeficiente_area_na_janela(
        self,
        bloco,
        area,
        bloco_inicio,
        janela_inicio,
        janela_final,
    ):

        if len(bloco.componentes) == 1:

            componente = bloco.componentes[0]

            if not self._componente_pertence_area(
                componente,
                area,
            ):
                return 0

            bloco_final = (
                bloco_inicio
                + bloco.tamanho
                - 1
            )

            inicio = max(
                bloco_inicio,
                janela_inicio,
            )

            fim = min(
                bloco_final,
                janela_final,
            )

            if inicio > fim:
                return 0

            return (
                fim
                - inicio
                + 1
            )

        total = 0

        for offset, componente in enumerate(
            bloco.componentes
        ):

            aula = (
                bloco_inicio
                + offset
            )

            if (
                janela_inicio
                <= aula
                <= janela_final
                and self._componente_pertence_area(
                    componente,
                    area,
                )
            ):

                total += 1

        return total

    # ==================================================
    # ÁREA
    # ==================================================

    def _bloco_pertence_area(
        self,
        bloco,
        area,
    ):

        for componente in bloco.componentes:

            if self._componente_pertence_area(
                componente,
                area,
            ):

                return True

        return False

    def _componente_pertence_area(
        self,
        componente,
        area,
    ):

        area_componente = (
            self.componente_para_area.get(
                componente
            )
        )

        return (
            area_componente == area
        )

    def _criar_mapa_componente_area(self):

        mapa = {}

        for esp in self.base.especialidades:

            mapa[
                esp.sigla.upper()
            ] = esp.componente.upper()

        return mapa

    # ==================================================
    # SLOTS
    # ==================================================

    def _dias(self):

        dias = []

        for slot in self.base.slots:

            if slot.dia not in dias:

                dias.append(
                    slot.dia
                )

        return dias

    def _aulas_do_dia(
        self,
        dia,
    ):

        return sorted(
            [
                slot.aula
                for slot in self.base.slots
                if slot.dia == dia
            ]
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

    # ==================================================
    # TURMAS
    # ==================================================

    def _turmas(self):

        return sorted(
            turma.codigo
            for turma in self.base.turmas
            if turma.ativa
        )

    # ==================================================
    # UTIL
    # ==================================================

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
        )