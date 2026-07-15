import logging

# Importações dos Handlers Ativos
from src.solver.rules.handlers.fixed_schedule_handler import FixedScheduleHandler
from src.solver.rules.handlers.different_days_handler import DifferentDaysHandler
from src.solver.rules.handlers.max_consecutive_handler import MaxConsecutiveHandler
from src.solver.rules.handlers.block_continuous_handler import BlockContinuousHandler

class NoOpHandler:
    """
    Padrão Null Object (No-Operation).
    Usado para regras que existem no Excel, mas que são tratadas de forma 
    estrutural em outras partes do sistema (como objetivos ou constraints core).
    Evita que o RuleEngine quebre e limpa os logs de aviso.
    """
    def __init__(self, *args, **kwargs):
        pass

    def apply(self, regra) -> int:
        # Retorna 0 informando que nenhuma restrição matemática extra foi gerada
        return 0


class RuleRegistry:
    """
    Catálogo central dos tipos de regra suportados pelo sistema.
    Mapeia o nome da regra (do Excel) para a classe Handler correspondente.
    """

    # 1. REGRAS ATIVAS (Geram restrições rígidas no Solver)
    _ACTIVE_RULES = {
        "DIA": FixedScheduleHandler,
        "AULA_INICIAL": FixedScheduleHandler,
        "AULA_FINAL": FixedScheduleHandler,
        "DIAS_DIFERENTES": DifferentDaysHandler,
        "MAX_CONSECUTIVAS": MaxConsecutiveHandler,
        "BLOCO_CONTINUO_MINIMO": BlockContinuousHandler,
    }

    # 2. REGRAS ESTRUTURAIS OU DESATIVADAS (Tratadas por Constraints/Objetivos dedicados)
    _STRUCTURAL_OR_IGNORED_RULES = {
        "PARES": NoOpHandler,               # Resolvida por PedagogicalPairsConstraint
        "BLOCO_OTIMO": NoOpHandler,         # Resolvida por AreaCompactnessObjective
        "BLOCO_ACEITAVEL": NoOpHandler,     # Resolvida por AreaCompactnessObjective
        "BLOCO_MINIMO": NoOpHandler,        # Coberta por MaxConsecutive/AreaCompactness
        "COMPLEMENTO": NoOpHandler,         # Desativada/Não utilizada
        "COMPLEMENTO_POSICAO": NoOpHandler, # Desativada/Não utilizada
    }

    # União de todos os mapeamentos para validação de suporte
    _RULES = {**_ACTIVE_RULES, **_STRUCTURAL_OR_IGNORED_RULES}

    @classmethod
    def is_supported(cls, tipo: str) -> bool:
        return tipo in cls._RULES

    @classmethod
    def get_handler(cls, tipo: str):
        if not cls.is_supported(tipo):
            raise ValueError(f"Tipo de regra não suportado pelo sistema: '{tipo}'")

        handler = cls._RULES[tipo]
        
        # Log discreto se estivermos usando um NoOpHandler para regras estruturais
        if handler == NoOpHandler:
            logging.debug(f"Regra '{tipo}' identificada como estrutural/NoOp. Ignorando aplicação via Engine.")

        return handler

    @classmethod
    def supported_types(cls) -> list[str]:
        return sorted(cls._RULES.keys())