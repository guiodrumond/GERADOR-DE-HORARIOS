from src.solver.rules.handlers.fixed_schedule_handler import FixedScheduleHandler
from src.solver.rules.handlers.different_days_handler import DifferentDaysHandler
from src.solver.rules.handlers.max_consecutive_handler import MaxConsecutiveHandler
from src.solver.rules.handlers.block_continuous_handler import BlockContinuousHandler
from src.solver.rules.handlers.pares_handler import ParesHandler
class RuleRegistry:
    """
    Catálogo central dos tipos de regra suportados pelo sistema.
    Mapeia o nome da regra (do Excel) para a classe Handler que a executa.
    """

    _RULES = {

        # Regras de posicionamento fixo
        
        "DIA": FixedScheduleHandler,
        "AULA_INICIAL": FixedScheduleHandler,
        "AULA_FINAL": FixedScheduleHandler,


        # Regras de distribuição


        "DIAS_DIFERENTES": DifferentDaysHandler,
        "MAX_CONSECUTIVAS": MaxConsecutiveHandler,
        "PARES": ParesHandler,

        # Regras de blocos pedagógicos


        "BLOCO_OTIMO": None,
        "BLOCO_ACEITAVEL": None,
        "BLOCO_MINIMO": None,
        "BLOCO_CONTINUO_MINIMO": BlockContinuousHandler,


        # Regras de complemento


        "COMPLEMENTO": None,
        "COMPLEMENTO_POSICAO": None,
    }

    @classmethod
    def is_supported(cls, tipo: str) -> bool:
        return tipo in cls._RULES

    @classmethod
    def get_handler(cls, tipo: str):
        if not cls.is_supported(tipo):
            raise ValueError(f"Tipo de regra não suportado pelo sistema: '{tipo}'")

        handler = cls._RULES[tipo]
        
        # Blindagem: Evita que o Engine tente executar um NoneType e quebre o sistema
        if handler is None:
            raise NotImplementedError(
                f"A regra '{tipo}' existe no catálogo, mas seu Handler (código) "
                "ainda não foi implementado."
            )

        return handler

    @classmethod
    def supported_types(cls) -> list[str]:
        return sorted(cls._RULES.keys())