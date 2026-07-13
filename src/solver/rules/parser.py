from src.domain.models import (
    RegraParametrizada,
)


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

    def parse(self, restricoes):

        regras = []

        for restricao in restricoes:

            regra = self._parse_regra(
                restricao.regra,
                restricao.valor,
            )

            regras.append(
                regra
            )

        return regras

    def _parse_regra(
        self,
        nome_regra: str,
        valor: str,
    ):

        alvo, tipo = (
            self._quebrar_regra(
                nome_regra
            )
        )

        return RegraParametrizada(
            alvo=alvo,
            tipo=tipo,
            valor=valor,
            regra_original=nome_regra,
        )

    def _quebrar_regra(
        self,
        nome_regra: str,
    ):

        nome_regra = (
            nome_regra.strip()
            .upper()
        )

        for tipo in sorted(
            self.TIPOS_VALIDOS,
            key=len,
            reverse=True,
        ):

            sufixo = f"_{tipo}"

            if nome_regra.endswith(
                sufixo
            ):

                alvo = nome_regra[
                    :-len(sufixo)
                ]

                return (
                    alvo,
                    tipo,
                )

        raise ValueError(
            f"Tipo de regra desconhecido: "
            f"{nome_regra}"
        )