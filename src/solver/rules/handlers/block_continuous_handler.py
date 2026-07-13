class BlockContinuousHandler:
    """
    Garante que todas as aulas de uma área/componente
    ocorram em um único bloco contínuo no mesmo dia.

    Exemplo:
        CHSA_BLOCO_CONTINUO = S

    Para cada turma:
        GEO + FIL + HIS/SOC precisam caber em uma janela contínua.
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

        if regra.valor != "S":
            return 0

        quantidade = 0

        alvo = regra.alvo

        for turma in self._turmas():

            blocos = self._blocos_do_alvo(
                turma=turma,
                alvo=alvo,
            )

            if not blocos:
                continue

            tamanho_total = self._tamanho_total(
                blocos
            )

            if tamanho_total == 0:
                continue

            janelas = self._criar_janelas(
                turma=turma,
                alvo=alvo,
                tamanho_total=tamanho_total,
            )

            if not janelas:

                raise ValueError(
                    f"Não há janela possível para "
                    f"{alvo} na turma {turma} "
                    f"com tamanho {tamanho_total}."
                )

            self.model.Add(
                sum(
                    janela_var
                    for janela_var, _, _ in janelas
                ) == 1
            )

            quantidade += 1

            for janela_var, dia, aula_inicio in janelas:

                aula_final = (
                    aula_inicio
                    + tamanho_total
                    - 1
                )

                for bloco in blocos:

                    vars_compativeis = (
                        self._vars_bloco_na_janela(
                            bloco=bloco,
                            dia=dia,
                            aula_inicio=aula_inicio,
                            aula_final=aula_final,
                        )
                    )

                    if not vars_compativeis:

                        self.model.Add(
                            janela_var == 0
                        )

                        continue

                    self.model.Add(
                        sum(vars_compativeis) == 1
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

    def _tamanho_total(
        self,
        blocos,
    ):

        total = 0

        for bloco in blocos:

            total += bloco.tamanho

        return total

    # ==================================================
    # JANELAS CONTÍNUAS
    # ==================================================

    def _criar_janelas(
        self,
        turma,
        alvo,
        tamanho_total,
    ):

        janelas = []

        for dia in self._dias():

            aulas = self._aulas_do_dia(
                dia
            )

            for aula_inicio in aulas:

                aula_final = (
                    aula_inicio
                    + tamanho_total
                    - 1
                )

                if aula_final not in aulas:
                    continue

                nome = self._nome_seguro(
                    f"janela_{turma}_{alvo}_{dia}_{aula_inicio}_{aula_final}"
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

    def _vars_bloco_na_janela(
        self,
        bloco,
        dia,
        aula_inicio,
        aula_final,
    ):

        resultado = []

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

            bloco_inicio = slot_aula

            bloco_final = (
                slot_aula
                + bloco.tamanho
                - 1
            )

            if (
                bloco_inicio >= aula_inicio
                and bloco_final <= aula_final
            ):

                resultado.append(
                    var
                )

        return resultado

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