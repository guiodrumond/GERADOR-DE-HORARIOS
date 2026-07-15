import logging
from src.solver.rules.registry import RuleRegistry

class RuleEngine:
    """
    Motor central de regras parametrizadas.

    Responsabilidades desta classe:
    1. Receber regras já processadas (parsed).
    2. Validar se o tipo de regra é suportado pelo sistema.
    3. Agrupar as regras pelo respetivo alvo.
    4. Encaminhar e aplicar cada regra no modelo através do respetivo Handler.
    """

    def __init__(self, model, variables, base, regras):
        self.model = model
        self.variables = variables
        self.base = base
        self.regras = regras

        self.total_aplicadas = 0
        self.total_pendentes = 0
        self.diagnostico = []

    def build(self) -> int:
        self._validar_regras()
        regras_por_alvo = self._agrupar_por_alvo()

        for alvo, regras_do_alvo in regras_por_alvo.items():
            for regra in regras_do_alvo:
                try:
                    # Obtém a classe tradutora correspondente
                    handler_class = RuleRegistry.get_handler(regra.tipo)
                    
                    if handler_class is None:
                        self._registrar_pendente(regra)
                        continue

                    # Instancia o handler para as regras deste alvo
                    handler = handler_class(
                        model=self.model,
                        variables=self.variables,
                        base=self.base,
                        regras_do_alvo=regras_do_alvo,
                    )

                    # Aplica a restrição e acumula o número de constraints geradas
                    quantidade = handler.apply(regra)
                    self.total_aplicadas += quantidade
                    self._registrar_aplicada(regra, quantidade)

                except NotImplementedError as e:
                    # Captura regras não implementadas de forma amigável
                    logging.info(f"Regra pendente de implementação: {regra.regra_original} | {e}")
                    self._registrar_pendente(regra)
                    
                except Exception as e:
                    # Erros inesperados de lógica de programação dentro do Handler são expostos
                    logging.error(f"Erro crítico ao aplicar a restrição '{regra.regra_original}': {e}")
                    raise e

        return self.total_aplicadas

    def _validar_regras(self):
        for regra in self.regras:
            if not RuleRegistry.is_supported(regra.tipo):
                raise ValueError(
                    f"Tipo de regra não suportado pelo sistema: '{regra.tipo}' "
                    f"na regra '{regra.regra_original}'."
                )

    def _agrupar_por_alvo(self) -> dict:
        grupos = {}
        for regra in self.regras:
            # Agrupamento otimizado usando o método nativo setdefault
            grupos.setdefault(regra.alvo, []).append(regra)
        return grupos

    def _registrar_pendente(self, regra):
        self.total_pendentes += 1
        self.diagnostico.append({
            "alvo": regra.alvo,
            "tipo": regra.tipo,
            "valor": regra.valor,
            "status": "PENDENTE",
            "restricoes_criadas": 0,
        })

    def _registrar_aplicada(self, regra, quantidade: int):
        self.diagnostico.append({
            "alvo": regra.alvo,
            "tipo": regra.tipo,
            "valor": regra.valor,
            "status": "APLICADA",
            "restricoes_criadas": quantidade,
        })

    def resumo(self) -> dict:
        return {
            "aplicadas": self.total_aplicadas,
            "pendentes": self.total_pendentes,
            "diagnostico": self.diagnostico,
        }