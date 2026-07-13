class AreaGroupingObjective:
    """
    Objetivo para agrupar áreas do conhecimento no mesmo dia.

    Usa regras do tipo:

        CHSA_BLOCO_MINIMO      4
        CHSA_BLOCO_ACEITAVEL   5
        CHSA_BLOCO_OTIMO       6

    Interpretação:
        Para cada turma, área e dia:
            se a área tiver pelo menos X aulas naquele dia,
            gera bônus na função objetivo.
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

        regras_por_area = (
            self._regras_por_area()
        )

        for area, regras_area in regras_por_area.items():

            total += self._aplicar_area(
                area,
                regras_area,
            )

        return total

    # ==================================================
    # APLICAÇÃO POR ÁREA
    # ==================================================

    def _aplicar_area(
        self,
        area,
        regras_area,
    ):

        total = 0

        for turma in self._turmas():

            for dia in self._dias():

                expressao = (
                    self._expressao_area_dia(
                        turma=turma,
                        area=area,
                        dia=dia,
                    )
                )

                if expressao is None:
                    continue

                for regra in regras_area:

                    total += self._criar_bonus(
                        turma=turma,
                        area=area,
                        dia=dia,
                        regra=regra,
                        expressao=expressao,
                    )

        return total

    def _criar_bonus(
        self,
        turma,
        area,
        dia,
        regra,
        expressao,
    ):

        limite = int(
            regra.valor
        )

        bonus = self.model.NewBoolVar(
            self._nome_seguro(
                f"bonus_{turma}_{area}_{dia}_{regra.tipo}_{limite}"
            )
        )

        self.model.Add(
            expressao >= limite
        ).OnlyEnforceIf(
            bonus
        )

        self.model.Add(
            expressao <= limite - 1
        ).OnlyEnforceIf(
            bonus.Not()
        )

        peso = self.PESOS[
            regra.tipo
        ]

        self.objective_builder.add_term(
            expression=bonus,
            peso=peso,
            descricao=(
                f"{area} {regra.tipo} "
                f"{turma} {dia} >= {limite}"
            ),
        )

        return 1

    # ==================================================
    # EXPRESSÃO ÁREA/DIA
    # ==================================================

    def _expressao_area_dia(
        self,
        turma,
        area,
        dia,
    ):

        termos = []

        for bloco in self.base.blocos:

            if bloco.turma != turma:
                continue

            aulas_area = (
                self._aulas_area_no_bloco(
                    bloco,
                    area,
                )
            )

            if aulas_area == 0:
                continue

            for slot_id, var in self.variables[
                bloco.id
            ].items():

                dia_slot = (
                    self._dia_do_slot(
                        slot_id
                    )
                )

                if dia_slot != dia:
                    continue

                termos.append(
                    aulas_area * var
                )

        if not termos:
            return None

        return sum(
            termos
        )

    def _aulas_area_no_bloco(
        self,
        bloco,
        area,
    ):

        # bloco comum: ["MAT"], tamanho 2
        if len(bloco.componentes) == 1:

            componente = (
                bloco.componentes[0]
            )

            area_componente = (
                self.componente_para_area.get(
                    componente
                )
            )

            if area_componente == area:
                return bloco.tamanho

            return 0

        # par pedagógico: ["ART", "ING"]
        total = 0

        for componente in bloco.componentes:

            area_componente = (
                self.componente_para_area.get(
                    componente
                )
            )

            if area_componente == area:
                total += 1

        return total

    # ==================================================
    # REGRAS
    # ==================================================

    def _regras_por_area(self):

        resultado = {}

        for regra in self.regras:

            if regra.tipo not in self.TIPOS_SUPORTADOS:
                continue

            if regra.alvo not in resultado:

                resultado[regra.alvo] = []

            resultado[regra.alvo].append(
                regra
            )

        return resultado

    # ==================================================
    # MAPAS
    # ==================================================

    def _criar_mapa_componente_area(self):

        mapa = {}

        for esp in self.base.especialidades:

            mapa[
                esp.sigla.upper()
            ] = esp.componente.upper()

        return mapa

    # ==================================================
    # UTIL
    # ==================================================

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

    def _dia_do_slot(
        self,
        slot_id,
    ):

        return slot_id.split(
            "_"
        )[0]

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