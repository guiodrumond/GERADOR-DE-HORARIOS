import logging

class PlanIndGhostConstraint:
    def __init__(self, model, variables, base):
        self.model = model
        self.variables = variables  
        self.base = base

    def build(self):
        logging.info("Construindo Escudo Anti-Fantasmas (PA/PV) para os Blocos Virtuais...")
        
        slots_fantasmas = {}
        
        # 1. Lê Atividades Avulsas
        if hasattr(self.base, 'atividades_avulsas') and self.base.atividades_avulsas:
            for ativ in self.base.atividades_avulsas:
                p_nome = str(ativ.professor).strip().upper()
                if p_nome not in slots_fantasmas: slots_fantasmas[p_nome] = set()
                dia = str(ativ.dia).strip().upper()
                try:
                    for a in range(int(float(ativ.aula_inicial)), int(float(ativ.aula_final)) + 1):
                        slots_fantasmas[p_nome].add(f"{dia}_{a}")
                except Exception: pass
                    
        # 2. Lê PA e PV
        projetos = {}
        for rest in self.base.restricoes:
            if rest.regra.startswith("PA_") or rest.regra.startswith("PV_"):
                partes = rest.regra.split("_")
                tipo, ano, prop = partes[0], str(partes[1]), "_".join(partes[2:])
                if ano not in projetos: projetos[ano] = {}
                if tipo not in projetos[ano]: projetos[ano][tipo] = {}
                projetos[ano][tipo][prop] = rest.valor
                
        for prof in self.base.professores:
            p_nome = str(prof.nome).strip().upper()
            if not prof.anos_atuacao or str(prof.anos_atuacao).lower().strip() in ["nan", "none", ""]: continue
            
            anos_prof = [a.strip()[:-2] if a.strip().endswith(".0") else a.strip() for a in str(prof.anos_atuacao).split(",")]
            
            for ano in anos_prof:
                if ano in projetos:
                    for tipo, props in projetos[ano].items():
                        dia = str(props.get("DIA", "")).strip().upper()
                        if p_nome not in slots_fantasmas: slots_fantasmas[p_nome] = set()
                        try:
                            for a in range(int(float(props.get("AULA_INICIAL"))), int(float(props.get("AULA_FINAL"))) + 1):
                                slots_fantasmas[p_nome].add(f"{dia}_{a}")
                        except Exception: pass

        # 3. Blinda as Variáveis Virtuais
        for bloco in self.base.blocos:
            if str(bloco.turma).startswith("PLAN_IND_"):
                p_nome = str(bloco.turma).replace("PLAN_IND_", "").strip()
                if p_nome in slots_fantasmas and bloco.id in self.variables:
                    fantasmas_prof = slots_fantasmas[p_nome]
                    for slot_id, var_bloco in self.variables[bloco.id].items():
                        if slot_id in fantasmas_prof:
                            self.model.Add(var_bloco == 0)