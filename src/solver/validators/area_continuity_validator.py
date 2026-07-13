class AreaContinuityValidator:

    TIPOS_VALIDOS = {
        "BLOCO_CONTINUO_MINIMO",
    }

    def __init__(
        self,
        base,
        grid,
        regras,
    ):

        self.base = base
        self.grid = grid
        self.regras = regras

        self.componente_para_area = (
            self._criar_mapa_componente_area()
        )

    def validate(self):

        problemas = []

        regras_continuas = [
            regra
            for regra in self.regras
            if regra.tipo in self.TIPOS_VALIDOS
        ]

        for regra in regras_continuas:

            area = regra.alvo
            minimo = int(regra.valor)

            for turma in self._turmas():

                maior_bloco = (
                    self._maior_bloco_continuo(
                        turma=turma,
                        area=area,
                    )
                )

                if maior_bloco < minimo:

                    problemas.append(
                        {
                            "turma": turma,
                            "area": area,
                            "minimo": minimo,
                            "encontrado": maior_bloco,
                        }
                    )

        return problemas

    def print_report(self):

        problemas = self.validate()

        print()
        print("===== VALIDAÇÃO DE BLOCOS CONTÍNUOS =====")
        print()

        if not problemas:

            print("VALIDAÇÃO: OK")
            return

        print(
            "VALIDAÇÃO: FALHOU"
        )

        print(
            "Problemas encontrados:",
            len(problemas)
        )

        for problema in problemas:

            print()
            print(
                problema["turma"],
                "|",
                problema["area"],
                "| mínimo:",
                problema["minimo"],
                "| encontrado:",
                problema["encontrado"],
            )

    # ==================================================
    # CÁLCULO
    # ==================================================

    def _maior_bloco_continuo(
        self,
        turma,
        area,
    ):

        maior = 0

        for dia in self._dias():

            atual = 0

            for aula in self._aulas():

                cell = self.grid.get(
                    turma,
                    dia,
                    aula,
                )

                if (
                    cell
                    and self._cell_pertence_area(
                        cell,
                        area,
                    )
                ):

                    atual += 1

                    if atual > maior:
                        maior = atual

                else:

                    atual = 0

        return maior

    def _cell_pertence_area(
        self,
        cell,
        area,
    ):

        componente = (
            cell.texto
            if cell
            else None
        )

        if componente is None:
            return False

        componente = componente.upper()

        area_componente = (
            self.componente_para_area.get(
                componente
            )
        )

        return area_componente == area

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
    # BASE
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

    def _aulas(self):

        return sorted(
            {
                slot.aula
                for slot in self.base.slots
            }
        )