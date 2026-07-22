import logging

class AtribuicaoVirtual:
    def __init__(self, turma, especialidade, professor, aulas):
        self.turma = turma
        self.especialidade = especialidade
        self.professor = professor
        self.aulas = aulas

class BlocoVirtual:
    def __init__(self, id, turma, componentes, tamanho):
        self.id = id
        self.turma = turma
        self.componentes = componentes
        self.tamanho = tamanho

class PlanIndVirtualBuilder:
    def __init__(self, base):
        self.base = base

    def _calcular_tamanhos(self, total):
        if total <= 0: return []
        if total == 1: return [1]
        blocos = []
        rest = total
        if rest % 2 != 0:
            blocos.append(3)
            rest -= 3
        while rest > 0:
            blocos.append(2)
            rest -= 2
        return blocos

    def build(self):
        logging.info("Construindo Blocos Virtuais de Planejamento Individual (PLANO B)...")
        
        novos_blocos = []
        novas_atribuicoes = []

        for prof in self.base.professores:
            if not prof.nome: continue
            p_nome = str(prof.nome).strip().upper()
            
            try:
                meta = int(float(getattr(prof, 'plan_ind', getattr(prof, 'Plan_Ind', 0))))
            except (ValueError, TypeError):
                meta = 0
                
            if meta > 0:
                tamanhos = self._calcular_tamanhos(meta)
                turma_virtual = f"PLAN_IND_{p_nome}"
                comp_virtual = "PLAN IND"
                
                # 1. Engana o sistema criando uma atribuição virtual
                atrib = AtribuicaoVirtual(
                    turma=turma_virtual,
                    especialidade=comp_virtual,
                    professor=p_nome,
                    aulas=meta
                )
                novas_atribuicoes.append(atrib)
                
                # 2. Cria os blocos atômicos que o Solver vai ser obrigado a alocar juntos
                for i, tam in enumerate(tamanhos):
                    b = BlocoVirtual(
                        id=f"{turma_virtual}_BLOCO_{i}",
                        turma=turma_virtual,
                        componentes=[comp_virtual],
                        tamanho=tam
                    )
                    novos_blocos.append(b)
                    
        self.base.atribuicoes.extend(novas_atribuicoes)
        self.base.blocos.extend(novos_blocos)
        logging.info(f"✅ Foram injetados {len(novos_blocos)} blocos virtuais de Plan_Ind no motor principal!")