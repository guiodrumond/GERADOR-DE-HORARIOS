class PlanejamentoMatcher:
    def __init__(self, base):
        self.base = base

    def filtrar_professores(self, planejamento):
        profs = set()
        
        # Helper para processar filtros tipo "1,2,3" ou "Tecnologia,Negócios"
        def check_match(valor_excel, valor_atribuicao):
            if not valor_excel: return True
            lista_filtros = [str(x).strip() for x in str(valor_excel).split(',')]
            return str(valor_atribuicao).strip() in lista_filtros

        for atr in self.base.atribuicoes:
            turma = next((t for t in self.base.turmas if t.codigo == atr.turma), None)
            area_obj = next((a for a in self.base.areas if a.curso == turma.curso), None)
            area_valor = area_obj.area if area_obj else None
            esp_obj = next((e for e in self.base.especialidades if e.nome == atr.especialidade), None)
            area_obj = next((a for a in self.base.areas if a.curso == turma.curso), None)

            comp_valor = esp_obj.componente if esp_obj else None
            area_valor = area_obj.area if area_obj else None
            
            if (check_match(planejamento.ano, turma.ano) and
                check_match(planejamento.area, area_valor) and
                check_match(planejamento.componente, comp_valor) and
                check_match(planejamento.especialidade, atr.especialidade)):
                
                profs.add(atr.professor)

        return list(profs)