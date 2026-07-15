class MaxConsecutiveHandler:
    """
    MAX_CONSECUTIVAS
    Exemplo: MAT_MAX_CONSECUTIVAS = 2
    Garante que uma disciplina ou área não ultrapasse o limite de aulas 
    seguidas no mesmo dia. Usa a lógica de "janela deslizante" (tamanho = max + 1).
    """

    def __init__(self, model, variables, base, regras_do_alvo):
        self.model = model
        self.variables = variables
        self.base = base
        self.regras_do_alvo = regras_do_alvo
        
        self.componente_para_area = self._criar_mapa_componente_area()
        self.aulas_por_dia = self._mapear_aulas_por_dia()

    def apply(self, regra):
        try:
            max_consecutivas = int(regra.valor)
        except ValueError:
            return 0  # Ignora se o valor no Excel não for um número válido

        tamanho_janela = max_consecutivas + 1
        quantidade = 0

        for turma in self._turmas():
            blocos = self._blocos_do_alvo(turma, regra.alvo)
            
            if not blocos:
                continue

            for dia, aulas_do_dia in self.aulas_por_dia.items():
                if len(aulas_do_dia) < tamanho_janela:
                    continue

                # Desliza uma janela de tamanho (max + 1) pelo dia
                for inicio in range(0, len(aulas_do_dia) - tamanho_janela + 1):
                    janela = aulas_do_dia[inicio : inicio + tamanho_janela]
                    termos = []

                    for bloco in blocos:
                        for slot_inicio_id, variavel in self.variables[bloco.id].items():
                            coeficiente = self._quantidade_ocupada_na_janela(
                                bloco, slot_inicio_id, dia, janela
                            )
                            if coeficiente > 0:
                                termos.append(coeficiente * variavel)

                    # Se a disciplina aparece nesta janela, a soma dos blocos nela 
                    # não pode ultrapassar o máximo permitido
                    if termos:
                        self.model.Add(sum(termos) <= max_consecutivas)
                        quantidade += 1

        return quantidade

    # ==================================================
    # BLOCOS E MAPEAMENTOS
    # ==================================================

    def _turmas(self):
        return sorted({bloco.turma for bloco in self.base.blocos})

    def _mapear_aulas_por_dia(self):
        mapa = {}
        for slot in self.base.slots:
            mapa.setdefault(slot.dia, []).append(slot.aula)
        for dia in mapa:
            mapa[dia].sort()
        return mapa

    def _blocos_do_alvo(self, turma: str, alvo: str):
        blocos = []
        for bloco in self.base.blocos:
            if bloco.turma == turma and self._bloco_pertence_ao_alvo(bloco, alvo):
                blocos.append(bloco)
        return blocos

    def _bloco_pertence_ao_alvo(self, bloco, alvo):
        for componente in bloco.componentes:
            if componente == alvo:
                return True
            if self.componente_para_area.get(componente) == alvo:
                return True
        return False

    def _criar_mapa_componente_area(self):
        return {esp.sigla.upper(): esp.componente.upper() for esp in self.base.especialidades}

    # ==================================================
    # MATEMÁTICA DA JANELA DESLIZANTE
    # ==================================================

    def _parse_slot_id(self, slot_id: str):
        partes = slot_id.split("_")
        return partes[0], int(partes[1])

    def _quantidade_ocupada_na_janela(self, bloco, slot_inicio_id: str, dia: str, janela: list[int]):
        dia_inicio, aula_inicio = self._parse_slot_id(slot_inicio_id)

        if dia_inicio != dia:
            return 0

        aula_final = aula_inicio + bloco.tamanho - 1
        ocupadas = 0

        # Conta quantos slots do bloco caem exatamente dentro dos limites desta janela
        for aula in janela:
            if aula_inicio <= aula <= aula_final:
                ocupadas += 1

        return ocupadas