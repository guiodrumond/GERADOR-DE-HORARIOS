class FixedScheduleHandler:
    """
    Trata as regras: DIA, AULA_INICIAL, AULA_FINAL.
    Fixa os blocos de uma disciplina (ou área) num dia e horário exatos.
    Suporta formato antigo (ALVO_TIPO) e novo formato por ano (ALVO_ANO_TIPO).
    """

    def __init__(self, model, variables, base, regras_do_alvo):
        self.model = model
        self.variables = variables
        self.base = base
        self.regras_do_alvo = regras_do_alvo
        
        self.componente_para_area = self._criar_mapa_componente_area()
        self.mapa_turma_ano = self._criar_mapa_turma_ano()

    def apply(self, regra):
        if regra.tipo != "DIA":
            return 0

        dia = self._valor("DIA")
        aula_inicial = self._valor("AULA_INICIAL")
        aula_final = self._valor("AULA_FINAL")

        if not dia or not aula_inicial or not aula_final:
            return 0

        aula_inicial = int(aula_inicial)
        aula_final = int(aula_final)
        tamanho_esperado = aula_final - aula_inicial + 1
        quantidade = 0
        
        # O pulo do gato: A regra alvo agora pode conter o ano (Ex: PA_1, PV_2)
        alvo_real = regra.alvo
        ano_alvo = None
        
        # Tenta extrair o ano da regra se ela for do tipo PA_1
        partes = regra.alvo.split('_')
        if len(partes) == 2 and partes[1].isdigit():
            alvo_real = partes[0]
            ano_alvo = int(partes[1])

        for turma in self._turmas():
            # Se a regra especificar um ano, pula turmas de outros anos
            if ano_alvo is not None and self.mapa_turma_ano.get(turma) != ano_alvo:
                continue
                
            blocos = self._blocos_do_alvo(turma, alvo_real)
            
            if not blocos:
                continue

            total_aulas_blocos = sum(bloco.tamanho for bloco in blocos)

            if total_aulas_blocos != tamanho_esperado:
                raise ValueError(
                    f"Conflito de carga horária na regra fixa de '{regra.alvo}' para a turma '{turma}'. "
                    f"A regra exige {tamanho_esperado} aulas (da aula {aula_inicial} à {aula_final}), "
                    f"mas a escola possui {total_aulas_blocos} aulas configuradas para esta turma."
                )

            aula_atual = aula_inicial
            
            for bloco in blocos:
                slot_id = f"{dia}_{aula_atual}"

                if slot_id in self.variables[bloco.id]:
                    self.model.Add(self.variables[bloco.id][slot_id] == 1)
                    quantidade += 1
                else:
                    raise ValueError(
                        f"Impossível fixar {bloco.id} em {slot_id}. "
                        "Verifique se o limite de aulas diárias não foi ultrapassado."
                    )

                aula_atual += bloco.tamanho

        return quantidade

    # ==================================================
    # UTILITÁRIOS
    # ==================================================

    def _valor(self, tipo):
        for regra in self.regras_do_alvo:
            if regra.tipo == tipo:
                return str(regra.valor).strip()
        return None

    def _turmas(self):
        return sorted({bloco.turma for bloco in self.base.blocos})
        
    def _criar_mapa_turma_ano(self):
        return {turma.codigo: turma.ano for turma in self.base.turmas}

    def _blocos_do_alvo(self, turma, alvo):
        resultado = []
        for bloco in self.base.blocos:
            if bloco.turma == turma and self._bloco_pertence_ao_alvo(bloco, alvo):
                resultado.append(bloco)
        return resultado

    def _bloco_pertence_ao_alvo(self, bloco, alvo):
        for componente in bloco.componentes:
            if componente == alvo:
                return True
            if self.componente_para_area.get(componente) == alvo:
                return True
        return False

    def _criar_mapa_componente_area(self):
        return {esp.sigla.upper(): esp.componente.upper() for esp in self.base.especialidades}