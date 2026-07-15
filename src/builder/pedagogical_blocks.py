from src.domain.database import BaseDados
from src.domain.models import BlocoPedagogico

class PedagogicalBlockBuilder:
    def __init__(self, base: BaseDados):
        self.base = base

    def _buscar_turma(self, codigo: str):
        for turma in self.base.turmas:
            if turma.codigo == codigo:
                return turma
        raise ValueError(f"Turma não encontrada: {codigo}")

    # =====================================================
    # PADRÕES PEDAGÓGICOS
    # =====================================================
    def _valor_padrao(self, componente: str, tipo: str):
        for padrao in self.base.padroes_pedagogicos:
            if padrao.componente == componente and padrao.tipo == tipo:
                return padrao.valor
        return None

    def _numero_duplas_matematica(self):
        valor = self._valor_padrao("MEST", "DUPLAS")
        return int(valor) if valor is not None else 2

    def _componentes_em_pares(self):
        componentes = set()
        for par in self.base.pares_pedagogicos:
            componentes.add(par.especialidade_1)
            componentes.add(par.especialidade_2)
        return componentes

    # =====================================================
    # BUILD GERAL E POR TURMA
    # =====================================================
    def build(self):
        blocos = []
        for turma in self.base.turmas:
            blocos.extend(self._build_turma(turma.codigo))
        return blocos

    def _build_turma(self, turma: str):
        blocos = []
        pares = self._componentes_em_pares()

        for esp in self.base.especialidades:
            sigla = esp.sigla.upper()

            if sigla in pares:
                continue

            if sigla == "POR":
                blocos.extend(self._criar_portugues(turma))
            elif sigla == "PROJ":
                blocos.append(
                    BlocoPedagogico(
                        id=f"{turma}_PROJ", turma=turma, componentes=["PROJ"], tamanho=4, fixo=True
                    )
                )
            elif sigla == "MAT":
                blocos.extend(self._criar_matematica(turma))
            elif sigla == "FTP":
                blocos.extend(self._criar_ftp(turma))
            else:
                blocos.extend(self._criar_bloco_generico(turma, sigla, esp.aulas))

        blocos.extend(self._criar_pares_pedagogicos(turma))
        return blocos

    # =====================================================
    # REGRAS ESPECÍFICAS
    # =====================================================
    def _criar_portugues(self, turma: str):
        return [
            BlocoPedagogico(id=f"{turma}_POR_A", turma=turma, componentes=["POR"], tamanho=2),
            BlocoPedagogico(id=f"{turma}_POR_B", turma=turma, componentes=["POR"], tamanho=1),
        ]

    def _criar_matematica(self, turma: str):
        blocos = []
        numero_duplas = self._numero_duplas_matematica()
        for numero in range(numero_duplas):
            sufixo = chr(ord("A") + numero)
            blocos.append(
                BlocoPedagogico(id=f"{turma}_MAT_{sufixo}", turma=turma, componentes=["MAT"], tamanho=2)
            )
        return blocos

    def _criar_ftp(self, turma: str):
        turma_obj = self._buscar_turma(turma)
        if turma_obj.padrao_ftp == "BLOCO4":
            return [BlocoPedagogico(id=f"{turma}_FTP", turma=turma, componentes=["FTP"], tamanho=4)]
        if turma_obj.padrao_ftp == "2+2":
            return [
                BlocoPedagogico(id=f"{turma}_FTP_A", turma=turma, componentes=["FTP"], tamanho=2),
                BlocoPedagogico(id=f"{turma}_FTP_B", turma=turma, componentes=["FTP"], tamanho=2),
            ]
        raise ValueError(f"Padrao_FTP inválido para turma {turma}: {turma_obj.padrao_ftp}")

    def _criar_pares_pedagogicos(self, turma: str):
        blocos = []
        for par in self.base.pares_pedagogicos:
            # Recupera a carga horária real (aulas) para não perder aulas na semana
            aulas_1 = next((e.aulas for e in self.base.especialidades if e.sigla.upper() == par.especialidade_1.upper()), 1)
            aulas_2 = next((e.aulas for e in self.base.especialidades if e.sigla.upper() == par.especialidade_2.upper()), 1)

            # Cria a quantidade correta de blocos de 1h com IDs únicos
            for i in range(aulas_1):
                blocos.append(
                    BlocoPedagogico(
                        id=f"{turma}_{par.especialidade_1}_UNIT_{i+1}",
                        turma=turma,
                        componentes=[par.especialidade_1],
                        tamanho=1,
                    )
                )
            for i in range(aulas_2):
                blocos.append(
                    BlocoPedagogico(
                        id=f"{turma}_{par.especialidade_2}_UNIT_{i+1}",
                        turma=turma,
                        componentes=[par.especialidade_2],
                        tamanho=1,
                    )
                )
        return blocos

    def _criar_bloco_generico(self, turma: str, sigla: str, aulas: int):
        # Distribuidor inteligente: divide a carga horária automaticamente sem dar erro
        blocos = []
        aulas_restantes = aulas
        contador = 1
        
        while aulas_restantes > 0:
            tamanho = 2 if aulas_restantes >= 2 else 1
            sufixo = chr(ord("A") + contador - 1) if aulas > 2 else "" 
            id_bloco = f"{turma}_{sigla}_{sufixo}".strip("_")
            
            blocos.append(
                BlocoPedagogico(id=id_bloco, turma=turma, componentes=[sigla], tamanho=tamanho)
            )
            aulas_restantes -= tamanho
            contador += 1
            
        return blocos