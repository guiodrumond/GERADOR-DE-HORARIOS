class BlockContinuousHandler:
    """
    BLOCO_CONTINUO_MINIMO

    Exemplo:

        CHSA_BLOCO_CONTINUO_MINIMO = 4

    Significa:

        Para cada turma, deve existir pelo menos uma janela
        contínua de 4 aulas em que todas as aulas sejam da área CHSA.
    """

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

        self.componente_para_area = (
            self._criar_mapa_componente_area()
        )

    def apply(
        self,
        regra,
    ):

        minimo = int(
            regra.valor
        )

        alvo = regra.alvo

        quantidade = 0

        for turma in self._turmas():

            blocos = self._blocos_do_alvo(
                turma=turma,
                alvo=alvo,
            )

            if not blocos:
                continue

            janelas = self._criar_janelas(
                turma=turma,
                alvo=alvo,
                tamanho_minimo=minimo,
            )

            if not janelas:

                raise ValueError(
                    f"Não há janela possível para "
                    f"{alvo} na turma {turma} "
                    f"com tamanho mínimo {minimo}."
                )

            self.model.Add(
                sum(
                    janela_var
                    for janela_var, _, _ in janelas
                ) >= 1
            )

            quantidade += 1

            for (
                janela_var,
                dia,
                aula_inicio,
            ) in janelas:

                aula_final = (
                    aula_inicio
                    + minimo
                    - 1
                )

                termos = []

                for bloco in blocos:

                    termos.extend(
                        self._termos_area_na_janela(
                            bloco=bloco,
                            alvo=alvo,
                            dia=dia,
                            aula_inicio=aula_inicio,
                            aula_final=aula_final,
                        )
                    )

                if not termos:

                    self.model.Add(
                        janela_var == 0
                    )

                    continue

                self.model.Add(
                    sum(termos) >= minimo
                ).OnlyEnforceIf(
                    janela_var
                )

        return quantidade

    # ==================================================
    # BLOCOS
    # ==================================================

    def _blocos_do_alvo(
        self,
        turma,
        alvo,
    ):

        blocos = []

        for bloco in self.base.blocos:

            if bloco.turma != turma:
                continue

            if self._bloco_pertence_ao_alvo(
                bloco,
                alvo,
            ):

                blocos.append(
                    bloco
                )

        return blocos

    def _bloco_pertence_ao_alvo(
        self,
        bloco,
        alvo,
    ):

        for componente in bloco.componentes:

            if componente == alvo:
                return True

            area = self.componente_para_area.get(
                componente
            )

            if area == alvo:
                return True

        return False

    # ==================================================
    # JANELAS
    # ==================================================

    def _criar_janelas(
        self,
        turma,
        alvo,
        tamanho_minimo,
    ):

        janelas = []

        for dia in self._dias():

            aulas = self._aulas_do_dia(
                dia
            )

            for aula_inicio in aulas:

                aula_final = (
                    aula_inicio
                    + tamanho_minimo
                    - 1
                )

                if aula_final not in aulas:
                    continue

                nome = self._nome_seguro(
                    (
                        f"janela_"
                        f"{turma}_"
                        f"{alvo}_"
                        f"{dia}_"
                        f"{aula_inicio}_"
                        f"{aula_final}"
                    )
                )

                var = self.model.NewBoolVar(
                    nome
                )

                janelas.append(
                    (
                        var,
                        dia,
                        aula_inicio,
                    )
                )

        return janelas

    # ==================================================
    # TERMOS DA ÁREA NA JANELA
    # ==================================================

    def _termos_area_na_janela(
        self,
        bloco,
        alvo,
        dia,
        aula_inicio,
        aula_final,
    ):

        termos = []

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
                    alvo=alvo,
                    bloco_inicio=slot_aula,
                    janela_inicio=aula_inicio,
                    janela_final=aula_final,
                )
            )

            if coeficiente > 0:

                termos.append(
                    coeficiente * var
                )

        return termos

    def _coeficiente_area_na_janela(
        self,
        bloco,
        alvo,
        bloco_inicio,
        janela_inicio,
        janela_final,
    ):

        # Caso 1:
        # Bloco comum: um único componente repetido
        # Exemplo: FIS tamanho 2, GEO tamanho 2, FTP tamanho 4

        if len(bloco.componentes) == 1:

            componente = (
                bloco.componentes[0]
            )

            if not self._componente_pertence_ao_alvo(
                componente,
                alvo,
            ):
                return 0

            bloco_final = (
                bloco_inicio
                + bloco.tamanho
                - 1
            )

            inicio_intersecao = max(
                bloco_inicio,
                janela_inicio,
            )

            fim_intersecao = min(
                bloco_final,
                janela_final,
            )

            if inicio_intersecao > fim_intersecao:
                return 0

            return (
                fim_intersecao
                - inicio_intersecao
                + 1
            )

        # Caso 2:
        # Par pedagógico decomposto.
        # Exemplo: ART/ING, HIS/SOC.
        #
        # Cada componente ocupa uma aula na ordem.

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
                and self._componente_pertence_ao_alvo(
                    componente,
                    alvo,
                )
            ):

                total += 1

        return total

    def _componente_pertence_ao_alvo(
        self,
        componente,
        alvo,
    ):

        if componente == alvo:
            return True

        area = self.componente_para_area.get(
            componente
        )

        return area == alvo

    # ==================================================
    # MAPAS
    # ==================================================

    def _criar_mapa_componente_area(
        self,
    ):

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