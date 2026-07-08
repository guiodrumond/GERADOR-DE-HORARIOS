from src.solver.rules.registry import (
    RuleRegistry,
)


class RuleEngine:
    """
    Motor central de regras parametrizadas.

    Responsabilidades desta classe:

    1. Receber regras já parseadas.
    2. Validar se o tipo da regra é suportado.
    3. Agrupar regras por alvo.
    4. Encaminhar regras para handlers quando eles existirem.

    Nesta primeira versão, os handlers ainda não estão implementados.
    Portanto, o engine apenas valida e informa quais regras estão pendentes.
    """

    def __init__(
        self,
        model,
        variables,
        base,
        regras,
    ):

        self.model = model
        self.variables = variables
        self.base = base
        self.regras = regras

        self.total_aplicadas = 0
        self.total_pendentes = 0
        self.diagnostico = []

    def build(self):

        self._validar_regras()

        regras_por_alvo = (
            self._agrupar_por_alvo()
        )

        for alvo, regras_do_alvo in regras_por_alvo.items():

            for regra in regras_do_alvo:

                handler_class = (
                    RuleRegistry.get_handler(
                        regra.tipo
                    )
                )

                if handler_class is None:

                    self._registrar_pendente(
                        regra
                    )

                    continue

                handler = handler_class(
                    model=self.model,
                    variables=self.variables,
                    base=self.base,
                    regras_do_alvo=regras_do_alvo,
                )

                quantidade = handler.apply(
                    regra
                )

                self.total_aplicadas += quantidade

                self._registrar_aplicada(
                    regra,
                    quantidade,
                )

        return self.total_aplicadas

    def _validar_regras(self):

        for regra in self.regras:

            if not RuleRegistry.is_supported(
                regra.tipo
            ):

                raise ValueError(
                    "Tipo de regra não suportado: "
                    f"{regra.tipo} "
                    f"na regra {regra.regra_original}"
                )

    def _agrupar_por_alvo(self):

        grupos = {}

        for regra in self.regras:

            if regra.alvo not in grupos:

                grupos[regra.alvo] = []

            grupos[regra.alvo].append(
                regra
            )

        return grupos

    def _registrar_pendente(
        self,
        regra,
    ):

        self.total_pendentes += 1

        self.diagnostico.append(
            {
                "alvo": regra.alvo,
                "tipo": regra.tipo,
                "valor": regra.valor,
                "status": "PENDENTE",
                "restricoes_criadas": 0,
            }
        )

    def _registrar_aplicada(
        self,
        regra,
        quantidade: int,
    ):

        self.diagnostico.append(
            {
                "alvo": regra.alvo,
                "tipo": regra.tipo,
                "valor": regra.valor,
                "status": "APLICADA",
                "restricoes_criadas": quantidade,
            }
        )

    def resumo(self):

        return {
            "aplicadas": self.total_aplicadas,
            "pendentes": self.total_pendentes,
            "diagnostico": self.diagnostico,
        }