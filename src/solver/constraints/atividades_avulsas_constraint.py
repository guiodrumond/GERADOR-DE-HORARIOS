import logging

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
                p_str = str(p).strip().upper()
                if p_str not in ["NONE", "NAN", "", "A DEFINIR"]:
                    professores.add(p_str)
        return professores

    def _parse_slot_id(self, slot_id):
        partes = slot_id.split("_")
        return partes[0].strip().upper(), int(partes[1])

    def _bloco_ocupa_slot(self, bloco, slot_inicio_id, dia_alvo, aula_alvo):
        dia_inicio, aula_inicio = self._parse_slot_id(slot_inicio_id)
        if dia_inicio != dia_alvo: return False
        aula_final = aula_inicio + bloco.tamanho - 1
        return aula_inicio <= aula_alvo <= aula_final

    def build(self):
        logging.info("\n" + "="*60)
        logging.info("🛠️ INICIANDO DIAGNÓSTICO: ATIVIDADES AVULSAS (SOLVER)")
        logging.info("="*60)

        if not hasattr(self.base, 'atividades_avulsas') or not self.base.atividades_avulsas:
            logging.warning("⚠️ Nenhuma atividade avulsa foi carregada da base. A lista está vazia!")
            logging.info("="*60 + "\n")
            return

        for avulsa in self.base.atividades_avulsas:
            prof_original = getattr(avulsa, 'professor', 'DESCONHECIDO')
            dia_original = getattr(avulsa, 'dia', 'DESCONHECIDO')
            
            prof_avulso = str(prof_original).strip().upper()
            dia_alvo = str(dia_original).strip().upper()
            
            try:
                a_ini = int(float(avulsa.aula_inicial))
                a_fim = int(float(avulsa.aula_final))
            except Exception as e:
                logging.error(f"❌ Erro ao converter aulas para {prof_avulso}. Valores originais: Ini={getattr(avulsa, 'aula_inicial', None)}, Fim={getattr(avulsa, 'aula_final', None)}")
                continue

            logging.info(f"\n🔎 Analisando Atividade da Planilha: Prof=[{prof_avulso}] | Dia=[{dia_alvo}] | Aulas=[{a_ini}] a [{a_fim}]")
            
            total_vars_bloqueadas = 0

            for aula_alvo in range(a_ini, a_fim + 1):
                vars_conflito = []
                
                for bloco in self.base.blocos:
                    professores_deste_bloco = self._professores_do_bloco(bloco)
                    
                    # Verifica se o professor lido está na lista de professores do bloco atual
                    if prof_avulso in professores_deste_bloco:
                        for slot_inicio_id, var_bloco in self.variables.get(bloco.id, {}).items():
                            if self._bloco_ocupa_slot(bloco, slot_inicio_id, dia_alvo, aula_alvo):
                                vars_conflito.append(var_bloco)
                                logging.info(f"   🚫 Bloqueando Bloco [{bloco.id}] da Turma [{bloco.turma}] no slot [{slot_inicio_id}] (aula alvo {aula_alvo})")
                
                if vars_conflito:
                    self.model.Add(sum(vars_conflito) == 0)
                    total_vars_bloqueadas += len(vars_conflito)
            
            logging.info(f"✅ Total de tentativas de alocação bloqueadas para {prof_avulso} no dia {dia_alvo}: {total_vars_bloqueadas}")
            
            if total_vars_bloqueadas == 0:
                logging.warning(f"⚠️ NENHUMA variável foi bloqueada para {prof_avulso}! Possíveis motivos:")
                logging.warning(f"   1. Ele não dá aula para nenhuma turma (o mapa de professores dele está vazio).")
                logging.warning(f"   2. O dia '{dia_alvo}' não corresponde ao padrão dos slots (ex: SEG, TER, QUA...).")
        
        logging.info("="*60 + "\n")