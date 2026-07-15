import pandas as pd
import logging
from src.domain.database import BaseDados
from src.domain.models import (
    Curso, Turma, Professor, Especialidade, Peso, Restricao,
    Atribuicao, ParPedagogico, PadraoPedagogico, Slot,
    AreaCurso, AfinidadeArea
)

class ExcelLoader:
    def __init__(self, filepath):
        self.filepath = filepath

    def load(self):
        logging.info(f"Carregando dados do arquivo: {self.filepath}")
        try:
            xl = pd.ExcelFile(self.filepath)
            
            # 1. Carrega CONFIG de forma segura (pega coluna 0 e 1, independente do nome)
            df_config = pd.read_excel(xl, sheet_name='CONFIG')
            config_dict = df_config.set_index(df_config.columns[0])[df_config.columns[1]].to_dict()

            # 2. Carrega todos os DataFrames
            dfs = {
                'CURSOS': pd.read_excel(xl, sheet_name='CURSOS'),
                'TURMAS': pd.read_excel(xl, sheet_name='TURMAS'),
                'PROFESSORES': pd.read_excel(xl, sheet_name='PROFESSORES'),
                'ESPEC': pd.read_excel(xl, sheet_name='ESPECIALIDADES_1ANO'),
                'PESOS': pd.read_excel(xl, sheet_name='PESOS'),
                'REST': pd.read_excel(xl, sheet_name='RESTRICOES'),
                'ATRIB': pd.read_excel(xl, sheet_name='ATRIBUICOES'),
                'PARES': pd.read_excel(xl, sheet_name='PARES_PEDAGOGICOS'),
                'PADROES': pd.read_excel(xl, sheet_name='PADROES_PEDAGOGICOS'),
                'SLOTS': pd.read_excel(xl, sheet_name='SLOTS'),
                'AREAS': pd.read_excel(xl, sheet_name='AREAS'),
                'AFINIDADE': pd.read_excel(xl, sheet_name='AFINIDADE_AREAS')
            }

            # 3. A "PEDRA DE ROSETA" (Tradução exata do Excel para o Python baseada no seu mapa)
            mapeamento = {
                'TURMAS': {'Turma': 'codigo', 'Curso': 'curso', 'Padrao_FTP': 'padrao_ftp', 'Ativa': 'ativa'},
                'CURSOS': {'Nome_Curso': 'nome_curso', 'Curso': 'codigo', 'Especialidade_FTP': 'especialidade_ftp', 'Padrao_FTP': 'padrao_ftp'},
                'PROFESSORES': {'Professor': 'nome', 'Especialidade': 'especialidade', 'Componente': 'componente', 'CH': 'carga_horaria', 'Max_Dias': 'max_dias', 'Ativo': 'ativo'},
                'ESPEC': {'Id': 'id', 'Componente': 'componente', 'Especialidade': 'nome', 'Sigla': 'sigla', 'Aulas': 'aulas'},
                'PESOS': {'Objetivo': 'objetivo', 'Nível': 'nivel', 'Peso': 'peso'},
                'REST': {'Regra': 'regra', 'Valor': 'valor'},
                'ATRIB': {'Turma': 'turma', 'Especialidade': 'especialidade', 'Professor': 'professor'},
                'PARES': {'Par': 'codigo', 'Especialidade_1': 'especialidade_1', 'Especialidade_2': 'especialidade_2'},
                'PADROES': {'Componente': 'componente', 'Tipo': 'tipo', 'Valor': 'valor'},
                'SLOTS': {'Dia': 'dia', 'Aula': 'aula'},
                'AREAS': {'Curso': 'curso', 'Area': 'area'},
                'AFINIDADE': {'Área A': 'area_a', 'Área B': 'area_b', 'Custo': 'custo'}
            }

            # Aplica o mapeamento e converte para dicionários
            dados_prontos = {}
            dados_prontos = {}
            for chave, df in dfs.items():
                if chave in mapeamento:
                    df = df.rename(columns=mapeamento[chave])
                
                # 1. Limpa sujeira do Excel (remove linhas que estão 100% vazias)
                df = df.dropna(how='all')
                
                # 2. Converte os "NaN" do Pandas para "None" do Python (evita erros nos Dataclasses)
                df = df.where(pd.notnull(df), None)
                
                dados_prontos[chave] = [row.to_dict() for _, row in df.iterrows()]

            # 4. Instancia as Dataclasses de forma limpa
            base = BaseDados(
                config=config_dict,
                cursos=[Curso(**d) for d in dados_prontos['CURSOS']],
                turmas=[Turma(**d) for d in dados_prontos['TURMAS']],
                especialidades=[Especialidade(**d) for d in dados_prontos['ESPEC']],
                pares_pedagogicos=[ParPedagogico(**d) for d in dados_prontos['PARES']],
                padroes_pedagogicos=[PadraoPedagogico(**d) for d in dados_prontos['PADROES']],
                restricoes=[Restricao(**d) for d in dados_prontos['REST']],
                atribuicoes=[Atribuicao(**d) for d in dados_prontos['ATRIB']],
                slots=[Slot(**d) for d in dados_prontos['SLOTS']],
                professores=[Professor(**d) for d in dados_prontos['PROFESSORES']],
                pesos=[Peso(**d) for d in dados_prontos['PESOS']],
                areas=[AreaCurso(**d) for d in dados_prontos['AREAS']],
                afinidade_areas=[AfinidadeArea(**d) for d in dados_prontos['AFINIDADE']]
            )

            logging.info("✅ Base de dados perfeitamente mapeada e carregada.")
            return base

        except Exception as e:
            logging.error(f"Erro fatal no mapeamento do Excel: {e}")
            import traceback
            logging.error(traceback.format_exc())
            return None

    def load_disponibilidade(self, base, filepath):
        try:
            df = pd.read_excel(filepath, sheet_name='DISPONIBILIDADE')
            disponibilidade = {}
            horarios = [c for c in df.columns if c != 'Professor']
            
            for _, row in df.iterrows():
                # Ignora linhas onde o nome do professor está vazio
                if pd.isna(row['Professor']):
                    continue
                
                prof = str(row['Professor']).strip()
                slots_bloqueados = [str(h).strip().replace(" ", "_") for h in horarios if str(row[h]).strip().upper() == 'X']
                if slots_bloqueados:
                    disponibilidade[prof] = slots_bloqueados
            
            base.disponibilidade = disponibilidade
            logging.info(f"✅ Disponibilidade carregada para {len(disponibilidade)} professores.")
            
        except Exception as e:
            logging.warning(f"⚠️ Aba 'DISPONIBILIDADE' não encontrada: {e}")