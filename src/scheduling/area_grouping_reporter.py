class AreaGroupingReporter:
    """
    Analisa a grade final gerada pelo Solver e extrai métricas de qualidade
    sobre o quão bem as Áreas do Conhecimento foram agrupadas em sequências contínuas.
    Suporta leitura de blocos multi-aulas (dobradinhas).
    """

    def __init__(self, solver, variables, base):
        self.solver = solver
        self.variables = variables
        self.base = base
        
        self.AREAS_CONHECIMENTO = {
            "LEST": ["POR", "EDF", "ING", "ART"],
            "CNST": ["FIS", "QUI", "BIO"],
            "CHSA": ["GEO", "FIL", "HIS", "SOC"]
        }
        
        # Variáveis de classe para guardar os dados e enviar para o Excel depois
        self.stats = {"6+": 0, "5": 0, "4": 0, "fragmentadas (<4)": 0}
        self.indice_fragmentacao = 0.0

    def print_report(self):
        print("\n" + "="*80)
        print("=== MEDIDOR DE QUALIDADE: AGRUPAMENTO DE ÁREAS ===".center(80))
        print("="*80)

        # 1. Extrair a grade real que o Solver gerou
        grade = {} 
        
        for bloco in self.base.blocos:
            turma = bloco.turma
            area_deste_bloco = "OUTROS"
            
            # Blindagem contra strings vs listas e espaços no Excel
            comps = bloco.componentes if isinstance(bloco.componentes, list) else [bloco.componentes]
            for area_nome, siglas in self.AREAS_CONHECIMENTO.items():
                if any(str(sigla).strip().upper() in siglas for sigla in comps):
                    area_deste_bloco = area_nome
                    break
                    
            if area_deste_bloco == "OUTROS":
                continue 

            for slot_id, var in self.variables[bloco.id].items():
                if self.solver.Value(var) == 1:
                    dia, aula = slot_id.split("_")
                    aula_int = int(aula)
                    
                    # MAGIA AQUI: Descobre o tamanho do bloco para cobrir as dobradinhas!
                    tamanho = getattr(bloco, 'aulas', getattr(bloco, 'tamanho', getattr(bloco, 'duracao', 1)))
                    
                    if turma not in grade: grade[turma] = {}
                    if dia not in grade[turma]: grade[turma][dia] = {}
                    
                    # Preenche todos os slots que este bloco ocupa (tapa os buracos!)
                    for i in range(tamanho):
                        grade[turma][dia][aula_int + i] = area_deste_bloco

        # 2. Contabilizar os blocos contínuos REAIS
        self.stats = {"6+": 0, "5": 0, "4": 0, "fragmentadas (<4)": 0} # Zera antes de contar
        
        for turma, dias in grade.items():
            for dia, aulas_dict in dias.items():
                area_atual = None
                tamanho_sequencia = 0
                
                # Algoritmo corrigido de contagem de sequência contínua
                for aula_idx in range(1, 7): 
                    area_nesta_aula = aulas_dict.get(aula_idx)
                    
                    if area_nesta_aula is None:
                        if area_atual is not None:
                            self._registrar_stats(self.stats, tamanho_sequencia)
                        area_atual = None
                        tamanho_sequencia = 0
                    elif area_nesta_aula == area_atual:
                        tamanho_sequencia += 1
                    else:
                        if area_atual is not None:
                            self._registrar_stats(self.stats, tamanho_sequencia)
                        area_atual = area_nesta_aula
                        tamanho_sequencia = 1
                        
                # Registra o que sobrou no final do dia
                if area_atual is not None:
                    self._registrar_stats(self.stats, tamanho_sequencia)

        # 3. Imprimir o Dashboard
        total_aulas_avaliadas = (self.stats["6+"]*6) + (self.stats["5"]*5) + (self.stats["4"]*4) + self.stats["fragmentadas (<4)"]
        
        print(f"🎯 Total de Sequências de LEST, CNST e CHSA encontradas na Escola:")
        print(f"  💎 Sequências Perfeitas (6 aulas):  {self.stats['6+']} blocos")
        print(f"  🥇 Sequências Excelentes (5 aulas): {self.stats['5']} blocos")
        print(f"  🥈 Sequências Boas (4 aulas):       {self.stats['4']} blocos")
        print(f"  ⚠️ Aulas Fragmentadas (<4 aulas):   {self.stats['fragmentadas (<4)']} pedaços")
        print("-" * 80)
        
        if total_aulas_avaliadas > 0:
            self.indice_fragmentacao = (self.stats['fragmentadas (<4)'] / total_aulas_avaliadas) * 100
            print(f"📊 ÍNDICE DE FRAGMENTAÇÃO DAS ÁREAS: {self.indice_fragmentacao:.1f}%")
            if self.indice_fragmentacao == 0:
                print("   🏆 ESTADO DA ARTE! Nenhuma aula de área solta no currículo!")
        else:
            self.indice_fragmentacao = 0.0
            
        print("="*80 + "\n")

    def _registrar_stats(self, stats, tamanho):
        """Função auxiliar para categorizar os tamanhos de blocos no painel."""
        if tamanho >= 6:
            stats["6+"] += 1
        elif tamanho == 5:
            stats["5"] += 1
        elif tamanho == 4:
            stats["4"] += 1
        elif tamanho > 0:
            stats["fragmentadas (<4)"] += tamanho # Conta quantas aulas ficaram soltas

    def get_stats(self):
        """
        Retorna o dicionário formatado para o ExcelExporter consumir as métricas reais.
        """
        return {
            'perfeitas': self.stats.get("6+", 0),
            'excelentes': self.stats.get("5", 0),
            'boas': self.stats.get("4", 0),
            'fragmentadas': self.stats.get("fragmentadas (<4)", 0),
            'indice_fragmentacao': round(self.indice_fragmentacao, 1)
        }