class PlanejamentoMatcher:
    def __init__(self, base):
        self.base = base

    def filtrar_professores(self, planejamento):
        profs = set()
        
        # Função para limpar sujeiras do Excel/Pandas
        def clean_val(v):
            if v is None: return ""
            s = str(v).strip().upper()
            if s.endswith(".0"): s = s[:-2] # Conserta o bug do Pandas (1.0 -> 1)
            return s

        def check_match(valor_excel, valor_memoria):
            v_excel = clean_val(valor_excel)
            # Se não há filtro no Excel ou é vazio/NaN, passa direto
            if not v_excel or v_excel in ('NAN', 'NONE', 'NAT'): 
                return True
            
            v_mem = clean_val(valor_memoria)
            # Se há filtro exigido no Excel, mas o professor não tem essa info, falha
            if not v_mem: 
                return False
            
            # Divide os filtros por vírgula (ex: "1, 2" vira ["1", "2"])
            lista_filtros = [x.strip() for x in v_excel.split(',')]
            return v_mem in lista_filtros

        # OLHANDO APENAS PARA A ABA DE PROFESSORES:
        for prof in self.base.professores:
            
            # Coleta os dados diretamente do objeto Professor
            # Usa getattr para garantir que não dê erro caso o nome da propriedade mude
            nome = getattr(prof, 'nome', None) or getattr(prof, 'professor', None)
            anos = getattr(prof, 'anos_atuacao', None)
            comp = getattr(prof, 'componente', None)
            esp = getattr(prof, 'especialidade', None)
            
            # Se a classe Professor tiver a propriedade 'area', ele pega. Se não, fica None.
            area = getattr(prof, 'area', None) 
            
            if not nome:
                continue

            if (check_match(planejamento.ano, anos) and
                check_match(planejamento.componente, comp) and
                check_match(planejamento.especialidade, esp) and
                check_match(planejamento.area, area)):
                
                profs.add(nome)
                
        return list(profs)