from collections import defaultdict


class ProfessorValidator:

    def __init__(
        self,
        base,
        variables,
        solver,
    ):

        self.base = base
        self.variables = variables
        self.solver = solver

        self.mapa_professores = (
            self._criar_mapa_professores()
        )

    def validate(self):

        ocupacao = (
            self._montar_ocupacao()
        )

        conflitos = []

        for chave, blocos in ocupacao.items():

            if len(blocos) <= 1:
                continue

            professor, slot = chave

            conflitos.append(
                {
                    "professor": professor,
                    "slot": slot,
                    "blocos": blocos,
                }
            )

        return conflitos

    def print_report(self):

        conflitos = self.validate()

        professores = {
            atribuicao.professor
            for atribuicao in self.base.atribuicoes
        }

        print()
        print("===== VALIDAÇÃO DOCENTE =====")
        print()

        print(
            "Professores analisados:",
            len(professores)
        )

        print(
            "Conflitos encontrados:",
            len(conflitos)
        )

        if not conflitos:

            print()
            print(
                "VALIDAÇÃO: OK"
            )

            return

        print()
        print(
            "VALIDAÇÃO: FALHOU"
        )

        for conflito in conflitos:

            print()
            print(
                conflito["professor"]
            )

            print(
                conflito["slot"]
            )

            for bloco in conflito["blocos"]:

                print(
                    " -",
                    bloco
                )

    # ==================================================
    # MAPA PROFESSOR
    # ==================================================

    def _criar_mapa_professores(self):

        mapa = {}

        for atribuicao in self.base.atribuicoes:

            chave = (
                atribuicao.turma,
                atribuicao.especialidade,
            )

            mapa[chave] = (
                atribuicao.professor
            )

        return mapa

    # ==================================================
    # OCUPAÇÃO
    # ==================================================

    def _montar_ocupacao(self):

        ocupacao = defaultdict(list)

        for bloco in self.base.blocos:

            professores = (
                self._professores_do_bloco(
                    bloco
                )
            )

            if not professores:
                continue

            slot_inicio = (
                self._slot_escolhido(
                    bloco.id
                )
            )

            if slot_inicio is None:
                continue

            slots_ocupados = (
                self._slots_ocupados(
                    bloco,
                    slot_inicio,
                )
            )

            for professor in professores:

                for slot in slots_ocupados:

                    ocupacao[
                        (
                            professor,
                            slot,
                        )
                    ].append(
                        bloco.id
                    )

        return ocupacao

    # ==================================================
    # PROFESSORES
    # ==================================================

    def _professores_do_bloco(
        self,
        bloco,
    ):

        professores = set()

        for componente in bloco.componentes:

            chave = (
                bloco.turma,
                componente,
            )

            professor = (
                self.mapa_professores.get(
                    chave
                )
            )

            if professor:

                professores.add(
                    professor
                )

        return professores

    # ==================================================
    # SOLUÇÃO
    # ==================================================

    def _slot_escolhido(
        self,
        bloco_id,
    ):

        for slot_id, variavel in self.variables[
            bloco_id
        ].items():

            if self.solver.BooleanValue(
                variavel
            ):

                return slot_id

        return None

    # ==================================================
    # SLOTS OCUPADOS
    # ==================================================

    def _slots_ocupados(
        self,
        bloco,
        slot_inicio_id,
    ):

        dia, aula_inicio = (
            self._parse_slot_id(
                slot_inicio_id
            )
        )

        resultado = []

        aula_final = (
            aula_inicio
            + bloco.tamanho
            - 1
        )

        for aula in range(
            aula_inicio,
            aula_final + 1,
        ):

            resultado.append(
                f"{dia}_{aula}"
            )

        return resultado

    def _parse_slot_id(
        self,
        slot_id,
    ):

        dia, aula = (
            slot_id.split("_")
        )

        return (
            dia,
            int(aula),
        )