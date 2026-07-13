from src.solver.rules.handlers.fixed_schedule_handler import (
    FixedScheduleHandler,
)

from src.solver.rules.handlers.different_days_handler import (
    DifferentDaysHandler,
)

from src.solver.rules.handlers.max_consecutive_handler import (
    MaxConsecutiveHandler,
)

from src.solver.rules.handlers.block_continuous_handler import (
    BlockContinuousHandler,
)

class RuleRegistry:
    """
    Catálogo central dos tipos de regra suportados pelo sistema.

    Nesta fase, os handlers ainda não foram implementados.
    Por isso os valores estão como None.

    Depois, cada None será substituído por uma classe handler.
    """

    _RULES = {
        # ---------------------------------
        # Regras de posicionamento fixo
        # ---------------------------------

        "DIA": FixedScheduleHandler,
        "AULA_INICIAL": FixedScheduleHandler,
        "AULA_FINAL": FixedScheduleHandler,

        # ---------------------------------
        # Regras de distribuição
        # ---------------------------------

        "DIAS_DIFERENTES": DifferentDaysHandler,
        "MAX_CONSECUTIVAS": MaxConsecutiveHandler,
        "PARES": None,

        # ---------------------------------
        # Regras de blocos pedagógicos
        # ---------------------------------

        "BLOCO_OTIMO": None,
        "BLOCO_ACEITAVEL": None,
        "BLOCO_MINIMO": None,
        "BLOCO_CONTINUO": BlockContinuousHandler,

        # ---------------------------------
        # Regras de complemento
        # ---------------------------------

        "COMPLEMENTO": None,
        "COMPLEMENTO_POSICAO": None,
    }

    @classmethod
    def is_supported(
        cls,
        tipo: str,
    ):

        return tipo in cls._RULES

    @classmethod
    def get_handler(
        cls,
        tipo: str,
    ):

        if not cls.is_supported(
            tipo
        ):

            raise ValueError(
                f"Tipo de regra não suportado: {tipo}"
            )

        return cls._RULES[tipo]

    @classmethod
    def supported_types(cls):

        return sorted(
            cls._RULES.keys()
        )