from src.domain.models import RegraParametrizada

class RuleParser:
    TIPOS_VALIDOS = {
        "BLOCO_OTIMO",
        "BLOCO_ACEITAVEL",
        "BLOCO_MINIMO",
        "BLOCO_CONTINUO_MINIMO",
        "COMPLEMENTO",
        "COMPLEMENTO_POSICAO",
        "MAX_CONSECUTIVAS",
        "PARES",
        "DIAS_DIFERENTES",
        "DIA",
        "AULA_INICIAL",
        "AULA_FINAL",
    }

    # Otimização: Ordena os tipos por tamanho decrescente apenas UMA vez
    # Isso evita reprocessamento para cada linha do Excel
    TIPOS_ORDENADOS = sorted(TIPOS_VALIDOS, key=len, reverse=True)

    def parse(self, restricoes):
        regras = []
        for restricao in restricoes:
            if not restricao.regra:
                continue  # Pula linhas vazias
                
            regra = self._parse_regra(restricao.regra, restricao.valor)
            regras.append(regra)
            
        return regras

    def _parse_regra(self, nome_regra: str, valor: str):
        alvo, tipo = self._quebrar_regra(nome_regra)
        return RegraParametrizada(
            alvo=alvo,
            tipo=tipo,
            valor=valor,
            regra_original=nome_regra,
        )

    def _quebrar_regra(self, nome_regra: str):
        nome_regra = nome_regra.strip().upper()
        
        for tipo in self.TIPOS_ORDENADOS:
            sufixo = f"_{tipo}"
            if nome_regra.endswith(sufixo):
                alvo = nome_regra[:-len(sufixo)]
                return alvo, tipo

        # Erro amigável mostrando as opções válidas
        tipos_formatados = ", ".join(self.TIPOS_VALIDOS)
        raise ValueError(
            f"Tipo de regra desconhecido no Excel: '{nome_regra}'. "
            f"Certifique-se de que termina com um dos tipos válidos: {tipos_formatados}"
        )