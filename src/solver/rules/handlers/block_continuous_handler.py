class BlockContinuousHandler:
    """
    BLOCO_CONTINUO_MINIMO
    Exemplo: CHSA_BLOCO_CONTINUO_MINIMO = 4
    Garante que para cada turma exista pelo menos UMA janela contínua
    de 4 aulas consecutivas apenas com componentes da área CHSA.
    """

    def __init__(self, model, variables, base, regras_do_alvo):
        self.model = model
        self.variables = variables
        self.base = base
        self.regras_do_alvo = regras_do_alvo
        
        self.componente_para_area = self._criar_mapa_componente_area()
        self.aulas_por_dia = self._mapear_aulas_por_dia()

    def apply(self, regra):
        minimo = int(regra.valor)
        alvo = regra.alvo
        quantidade = 0

        for turma in self._turmas():
            blocos = self._blocos_do_alvo(turma, alvo)
            if not blocos:
                continue

            janelas = self._criar_janelas(turma, alvo, minimo)
            if not janelas:
                raise ValueError(
                    f"Impossível aplicar regra: Não há janela possível para "
                    f"'{alvo}' na turma '{turma}' com tamanho mínimo de {minimo} aulas."
                )

            # Pelo menos UMA das janelas possíveis deve ser verdadeira (1)
            self.model.Add(sum(janela_var for janela_var, _, _ in janelas) >= 1)
            quantidade += 1

            for janela_var, dia, aula_inicio in janelas:
                aula_final = aula_inicio + minimo - 1
                termos = []

                for bloco in blocos:
                    termos.extend(
                        self._termos_area_na_janela(bloco, alvo, dia, aula_inicio, aula_final)
                    )

                if not termos:
                    # Se não há blocos suficientes que possam cair nesta janela, ela é inválida
                    self.model.Add(janela_var == 0)
                    continue

                # Se a janela for ativada, a soma de blocos do alvo dentro dela deve ser >= mínimo
                self.model.Add(sum(termos) >= minimo).OnlyEnforceIf(janela_var)

        return quantidade

    # ==================================================
    # BLOCOS E MAPEAMENTOS
    # ==================================================

    def _blocos_do_alvo(self, turma, alvo):
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

    def _mapear_aulas_por_dia(self):
        mapa = {}
        for slot in self.base.slots:
            mapa.setdefault(slot.dia, []).append(slot.aula)
        for dia in mapa:
            mapa[dia].sort()
        return mapa

    def _turmas(self):
        return sorted([turma.codigo for turma in self.base.turmas if turma.ativa])

    # ==================================================
    # JANELAS E MATEMÁTICA DA SOBREPOSIÇÃO
    # ==================================================

    def _criar_janelas(self, turma, alvo, tamanho_minimo):
        janelas = []
        for dia, aulas in self.aulas_por_dia.items():
            for aula_inicio in aulas:
                aula_final = aula_inicio + tamanho_minimo - 1
                if aula_final not in aulas:
                    continue  # A janela ultrapassa o limite de aulas do dia

                nome = f"janela_{turma}_{alvo}_{dia}_{aula_inicio}_{aula_final}"
                var = self.model.NewBoolVar(self._nome_seguro(nome))
                janelas.append((var, dia, aula_inicio))
        return janelas

    def _termos_area_na_janela(self, bloco, alvo, dia, aula_inicio, aula_final):
        termos = []
        for slot_id, var in self.variables[bloco.id].items():
            slot_dia, slot_aula = slot_id.split("_")
            slot_aula = int(slot_aula)

            if slot_dia != dia:
                continue

            # Calcula quantas aulas do bloco caem dentro da janela solicitada
            coeficiente = self._coeficiente_area_na_janela(
                bloco, alvo, slot_aula, aula_inicio, aula_final
            )

            if coeficiente > 0:
                termos.append(coeficiente * var)

        return termos

    def _coeficiente_area_na_janela(self, bloco, alvo, bloco_inicio, janela_inicio, janela_final):
        """
        Retorna o número de slots (aulas) em que o bloco sobrepõe a janela de análise.
        """
        componente = bloco.componentes[0]
        if not self._bloco_pertence_ao_alvo(bloco, alvo):
            return 0

        bloco_final = bloco_inicio + bloco.tamanho - 1

        # Matemática de interseção de segmentos de reta
        inicio_intersecao = max(bloco_inicio, janela_inicio)
        fim_intersecao = min(bloco_final, janela_final)

        if inicio_intersecao > fim_intersecao:
            return 0  # Não há sobreposição

        return fim_intersecao - inicio_intersecao + 1

    def _nome_seguro(self, texto):
        return texto.replace(" ", "_").replace("+", "_").replace("-", "_").replace("/", "_")