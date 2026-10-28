import pandas as pd
import logging
from src.domain.database import BaseDados
from src.domain.models import (
    Curso, Turma, Professor, Especialidade, Peso, Restricao,
    Atribuicao, ParPedagogico, PadraoPedagogico, Slot,
    AreaCurso, AfinidadeArea, Planejamento, AtividadeAvulsa
)


class ExcelLoader:
    def __init__(self, filepath):
        self.filepath = filepath

    @staticmethod
    def _texto_opcional(row, coluna, maiusculo=False):
        """
        Lê uma coluna opcional da linha.
        Retorna None se a coluna não existir ou estiver vazia.
        """
        if coluna not in row.index:
            return None

        valor = row[coluna]

        if pd.isna(valor):
            return None

        texto = str(valor).strip()

        if not texto:
            return None

        return texto.upper() if maiusculo else texto

    def _carregar_planejamentos(self, df_plan):
        planejamentos = []

        df_plan = df_plan.dropna(how='all')

        for _, row in df_plan.iterrows():

            nome = self._texto_opcional(row, 'Reuniao')
            tamanho = row['Tamanho'] if 'Tamanho' in row.index else None

            if not nome or pd.isna(tamanho):
                continue

            planejamentos.append(
                Planejamento(
                    nome=nome,
                    tamanho=int(float(tamanho)),
                    ano=self._texto_opcional(row, 'Anos_atuacao'),
                    area=self._texto_opcional(row, 'Area'),
                    componente=self._texto_opcional(row, 'Componente'),
                    especialidade=self._texto_opcional(row, 'Especialidade'),
                    grupo=self._texto_opcional(row, 'Grupo', maiusculo=True),
                )
            )

        sem_grupo = [p.nome for p in planejamentos if not p.grupo]

        if sem_grupo:
            logging.warning(
                f"⚠️ Reuniões sem GRUPO definido ({len(sem_grupo)}): {', '.join(sem_grupo)}"
            )

        logging.info(f"✅ Planejamentos carregados: {len(planejamentos)}")

        return planejamentos

    def load(self):
        logging.info(f"Carregando dados do arquivo: {self.filepath}")
        try:
            xl = pd.ExcelFile(self.filepath)

            df_config = pd.read_excel(xl, sheet_name='CONFIG')
            config_dict = df_config.set_index(df_config.columns[0])[df_config.columns[1]].to_dict()

            dfs = {
                'CURSOS': pd.read_excel(xl, sheet_name='CURSOS'),
                'TURMAS': pd.read_excel(xl, sheet_name='TURMAS'),
                'PROFESSORES': pd.read_excel(xl, sheet_name='PROFESSORES'),
                'ESPEC': pd.read_excel(xl, sheet_name='ESPECIALIDADES'),
                'PESOS': pd.read_excel(xl, sheet_name='PESOS'),
                'REST': pd.read_excel(xl, sheet_name='RESTRICOES'),
                'ATRIB': pd.read_excel(xl, sheet_name='ATRIBUICOES'),
                'PARES': pd.read_excel(xl, sheet_name='PARES_PEDAGOGICOS'),
                'PADROES': pd.read_excel(xl, sheet_name='PADROES_PEDAGOGICOS'),
                'SLOTS': pd.read_excel(xl, sheet_name='SLOTS'),
                'AREAS': pd.read_excel(xl, sheet_name='AREAS'),
                'AFINIDADE': pd.read_excel(xl, sheet_name='AFINIDADE_AREAS'),
                'PLAN': pd.read_excel(xl, sheet_name='PLANEJAMENTO'),
                'AVULSAS': pd.read_excel(xl, sheet_name='ATIVIDADES_AVULSAS') if 'ATIVIDADES_AVULSAS' in xl.sheet_names else pd.DataFrame(),
            }

            mapeamento = {
                'TURMAS': {'Turma': 'codigo', 'Curso': 'curso', 'Padrao_FTP': 'padrao_ftp', 'Ativa': 'ativa', 'Ano': 'ano'},
                'CURSOS': {'Nome_Curso': 'nome_curso', 'Curso': 'codigo', 'Especialidade_FTP': 'especialidade_ftp', 'Padrao_FTP': 'padrao_ftp'},
                'PROFESSORES': {'Professor': 'nome', 'Especialidade': 'especialidade', 'Componente': 'componente', 'Anos_atuacao': 'anos_atuacao', 'Area': 'area', 'CH': 'carga_horaria', 'Plan_Ind': 'plan_ind', 'Max_Dias': 'max_dias', 'Ativo': 'ativo'},
                'ESPEC': {'Id': 'id', 'Ano': 'ano', 'Componente': 'componente', 'Especialidade': 'nome', 'Sigla': 'sigla', 'Aulas': 'aulas'},
                'PESOS': {'Objetivo': 'objetivo', 'Nível': 'nivel', 'Peso': 'peso'},
                'REST': {'Regra': 'regra', 'Valor': 'valor'},
                'ATRIB': {'Turma': 'turma', 'Especialidade': 'especialidade', 'Professor': 'professor'},
                'PARES': {'Par': 'codigo', 'Ano': 'ano', 'Especialidade_1': 'especialidade_1', 'Especialidade_2': 'especialidade_2'},
                'PADROES': {'Componente': 'componente', 'Tipo': 'tipo', 'Valor': 'valor'},
                'SLOTS': {'Dia': 'dia', 'Aula': 'aula'},
                'AREAS': {'Curso': 'curso', 'Area': 'area'},
                'AFINIDADE': {'Área A': 'area_a', 'Área B': 'area_b', 'Custo': 'custo'},
                'AVULSAS': {'Professor': 'professor', 'Atividade': 'atividade', 'Dia': 'dia', 'Aula_Inicial': 'aula_inicial', 'Aula_Final': 'aula_final'},
            }

            dados_prontos = {}
            for chave, df in dfs.items():
                if chave in mapeamento:
                    df = df.rename(columns=mapeamento[chave])

                    # BLINDAGEM CONTRA "SUJEIRA" DO EXCEL (Ignora colunas Unnamed ou não mapeadas)
                    colunas_validas = [c for c in mapeamento[chave].values() if c in df.columns]
                    df = df[colunas_validas]

                df = df.dropna(how='all')
                df = df.where(pd.notnull(df), None)

                dados_prontos[chave] = [row.to_dict() for _, row in df.iterrows()]

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
                professores=[Professor(**{**d, 'plan_ind': int(float(d.get('plan_ind') or 0))}) for d in dados_prontos['PROFESSORES']],
                pesos=[Peso(**d) for d in dados_prontos['PESOS']],
                areas=[AreaCurso(**d) for d in dados_prontos['AREAS']],
                afinidade_areas=[AfinidadeArea(**d) for d in dados_prontos['AFINIDADE']],
                planejamentos=self._carregar_planejamentos(dfs['PLAN']),
                atividades_avulsas=[AtividadeAvulsa(**d) for d in dados_prontos.get('AVULSAS', [])]
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