class FixedScheduleHandler:
    """
    Trata as regras: DIA, AULA_INICIAL, AULA_FINAL.
    Fixa os blocos de uma disciplina (ou área) num dia e horário exatos.
    """

    def __init__(self, model, variables, base, regras_do_alvo):
        self.model = model
        self.variables = variables
        self.base = base
        self.regras_do_alvo = regras_do_alvo
        
        self.componente_para_area = self._criar_mapa_componente_area()

    def apply(self, regra):
        # Para não aplicar a mesma lógica 3 vezes (para DIA, INICIAL e FINAL), 
        # elegemos a regra 'DIA' como o gatilho para agir.
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

        for turma in self._turmas():
            blocos = self._blocos_do_alvo(turma, regra.alvo)
            
            if not blocos:
                continue

            # Soma a duração de todos os blocos desta disciplina
            total_aulas_blocos = sum(bloco.tamanho for bloco in blocos)

            if total_aulas_blocos != tamanho_esperado:
                raise ValueError(
                    f"Conflito de carga horária na regra fixa de '{regra.alvo}' para a turma '{turma}'. "
                    f"A regra exige {tamanho_esperado} aulas (da aula {aula_inicial} à {aula_final}), "
                    f"mas a escola possui {total_aulas_blocos} aulas configuradas para esta turma."
                )

            # Alocação Sequencial Inteligente (Suporta blocos fragmentados)
            aula_atual = aula_inicial
            
            for bloco in blocos:
                slot_id = f"{dia}_{aula_atual}"

                # Valida se o slot existe no dicionário de variáveis do bloco
                if slot_id in self.variables[bloco.id]:
                    # Fixa (chumba) o bloco neste slot exato
                    self.model.Add(self.variables[bloco.id][slot_id] == 1)
                    quantidade += 1
                else:
                    raise ValueError(
                        f"Impossível fixar {bloco.id} em {slot_id}. "
                        "Verifique se o limite de aulas diárias não foi ultrapassado."
                    )

                # Avança o ponteiro para o próximo horário disponível na sequência
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