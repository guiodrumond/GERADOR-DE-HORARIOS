class AreaCompactnessObjective:

    TIPOS_AREA = {
        "BLOCO_MINIMO",
        "BLOCO_ACEITAVEL",
        "BLOCO_OTIMO",
        "BLOCO_CONTINUO_MINIMO",
    }

    AREA_PESOS = {
        "CHSA": 10,
        "CNST": 10,
        "LEST": 10,
        "MEST": 6,
        "FTP": 6,
        "PROJ": 4,
    }

    TAMANHO_MINIMO_JANELA = 2

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

    def build(self):

        total = 0

        for area in self._areas_com_objetivo():

            total += self._aplicar_area(
                area
            )

        return total

    def _aplicar_area(
        self,
        area,
    ):

        total = 0

        peso_area = self._peso_area(
            area
        )

        for turma in self._turmas():

            for dia in self._dias():

                aulas = self._aulas_do_dia(
                    dia
                )

                tamanho_maximo = len(
                    aulas
                )

                for tamanho_janela in (
                    4,
                    5,
                    6,
                ):

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
                                f"bonus_compact_{turma}_{area}_{dia}_{aula_inicio}_{aula_final}"
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

                        peso = (
                            tamanho_janela
                            * tamanho_janela
                            * peso_area
                        )

                        self.objective_builder.add_term(
                            expression=bonus,
                            peso=peso,
                            descricao=(
                                f"{area} COMPACTACAO "
                                f"{turma} {dia} "
                                f"{aula_inicio}-{aula_final}"
                            ),
                        )

                        total += 1

        return total

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

            componente = (
                bloco.componentes[0]
            )

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

    def _areas_com_objetivo(self):

        areas = set()

        for regra in self.regras:

            if regra.tipo in self.TIPOS_AREA:

                areas.add(
                    regra.alvo
                )

        return sorted(
            areas
        )

    def _peso_area(
        self,
        area,
    ):

        return self.AREA_PESOS.get(
            area,
            10,
        )

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

    def _turmas(self):

        return sorted(
            turma.codigo
            for turma in self.base.turmas
            if turma.ativa
        )

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