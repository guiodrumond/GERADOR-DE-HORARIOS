class DifferentDaysHandler:
    """
    DIAS_DIFERENTES
    Garante que os blocos de uma determinada disciplina ou área
    ocorram em dias distintos na semana para uma mesma turma.
    """

    def __init__(self, model, variables, base, regras_do_alvo):
        self.model = model
        self.variables = variables
        self.base = base
        self.regras_do_alvo = regras_do_alvo

        self.componente_para_area = self._criar_mapa_componente_area()
        self.dias_da_semana = self._dias_da_semana()

    def apply(self, regra):
        # Validação robusta para diferentes formas de escrever "Sim" no Excel
        valor = str(regra.valor).strip().upper()
        if valor not in {"S", "SIM", "TRUE", "1", "V", "VERDADEIRO"}:
            return 0

        quantidade = 0

        for turma in self._turmas():
            blocos = self._blocos_do_alvo(turma, regra.alvo)

            # Se a turma tem apenas 1 bloco desta disciplina/área, 
            # é impossível cair no mesmo dia. Não precisamos criar restrições.
            if len(blocos) < 2:
                continue

            # Otimização Matemática: Em vez de criar restrições para cada "par" de blocos,
            # nós agrupamos todos os blocos do alvo por dia e dizemos: 
            # "A soma de todos eles neste dia tem que ser <= 1"
            for dia in self.dias_da_semana:
                vars_do_dia = []

                for bloco in blocos:
                    for slot_id, var in self.variables[bloco.id].items():
                        slot_dia = slot_id.split("_")[0]
                        if slot_dia == dia:
                            vars_do_dia.append(var)

                if vars_do_dia:
                    # No máximo UM bloco desse alvo pode iniciar neste dia
                    self.model.Add(sum(vars_do_dia) <= 1)
                    quantidade += 1

        return quantidade

    # ==================================================
    # BLOCOS E MAPEAMENTOS
    # ==================================================

    def _turmas(self):
        # Extrai turmas únicas a partir dos blocos existentes
        return sorted(list({bloco.turma for bloco in self.base.blocos}))

    def _blocos_do_alvo(self, turma, alvo):
        resultado = []
        for bloco in self.base.blocos:
            if bloco.turma != turma:
                continue
            if self._bloco_pertence_ao_alvo(bloco, alvo):
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

    def _dias_da_semana(self):
        dias = []
        for slot in self.base.slots:
            if slot.dia not in dias:
                dias.append(slot.dia)
        return dias