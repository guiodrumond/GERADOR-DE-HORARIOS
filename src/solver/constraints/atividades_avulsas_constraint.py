class AtividadesAvulsasConstraint:
    def __init__(self, model, variables, base):
        self.model = model
        self.variables = variables
        self.base = base
        self.mapa_professores = self._criar_mapa_professores()

    def _criar_mapa_professores(self):
        mapa = {}
        for atribuicao in self.base.atribuicoes:
            chave = (atribuicao.turma, atribuicao.especialidade)
            if chave not in mapa:
                mapa[chave] = []
            if atribuicao.professor:
                mapa[chave].append(atribuicao.professor)
        return mapa

    def _professores_do_bloco(self, bloco):
        professores = set()
        for componente in bloco.componentes:
            chave = (bloco.turma, componente)
            for p in self.mapa_professores.get(chave, []):
                if str(p).strip().upper() not in ["NONE", "NAN", "", "A DEFINIR"]:
                    professores.add(p)
        return professores

    def _parse_slot_id(self, slot_id):
        partes = slot_id.split("_")
        return partes[0], int(partes[1])

    def _bloco_ocupa_slot(self, bloco, slot_inicio_id, dia_alvo, aula_alvo):
        dia_inicio, aula_inicio = self._parse_slot_id(slot_inicio_id)
        if dia_inicio != dia_alvo: return False
        aula_final = aula_inicio + bloco.tamanho - 1
        return aula_inicio <= aula_alvo <= aula_final

    def build(self):
        for avulsa in self.base.atividades_avulsas:
            for aula_alvo in range(int(avulsa.aula_inicial), int(avulsa.aula_final) + 1):
                dia_alvo = avulsa.dia
                
                vars_conflito = []
                for bloco in self.base.blocos:
                    if avulsa.professor in self._professores_do_bloco(bloco):
                        for slot_inicio_id, var_bloco in self.variables.get(bloco.id, {}).items():
                            if self._bloco_ocupa_slot(bloco, slot_inicio_id, dia_alvo, aula_alvo):
                                vars_conflito.append(var_bloco)
                
                if vars_conflito:
                    self.model.Add(sum(vars_conflito) == 0)