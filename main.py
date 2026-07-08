from src.data.loader import ExcelLoader

from src.builder.pedagogical_blocks import (
    PedagogicalBlockBuilder,
)

from src.solver.variables import (
    DecisionVariableBuilder,
)

from src.solver.rules.parser import (
    RuleParser,
)

from src.solver.rules.registry import (
    RuleRegistry,
)

from src.solver.rules.engine import (
    RuleEngine,
)


ARQUIVO = "excel/GERADOR_DE_HORARIOS.xlsx"


def main():

    print()
    print("===== CARREGANDO BASE =====")
    print()

    loader = ExcelLoader(
        ARQUIVO
    )

    base = loader.load()

    # =====================================
    # BLOCOS PEDAGÓGICOS
    # =====================================

    builder = PedagogicalBlockBuilder(
        base
    )

    base.blocos = builder.build()

    # =====================================
    # REGRAS PARAMETRIZADAS
    # =====================================

    parser = RuleParser()

    regras = parser.parse(
        base.restricoes
    )

    print()
    print("===== REGRAS PARAMETRIZADAS =====")
    print()

    for regra in regras:

        print(
            regra.alvo,
            "|",
            regra.tipo,
            "|",
            regra.valor,
        )

    # =====================================
    # TIPOS SUPORTADOS
    # =====================================

    print()
    print("===== TIPOS SUPORTADOS =====")
    print()

    for tipo in RuleRegistry.supported_types():

        print(tipo)

    # =====================================
    # VARIÁVEIS CP-SAT
    # =====================================

    variable_builder = (
        DecisionVariableBuilder(
            base
        )
    )

    model, variables = (
        variable_builder.build()
    )

    # =====================================
    # RULE ENGINE
    # =====================================

    rule_engine = RuleEngine(
        model=model,
        variables=variables,
        base=base,
        regras=regras,
    )

    rule_engine.build()

    resumo = (
        rule_engine.resumo()
    )

    print()
    print("===== RULE ENGINE =====")
    print()

    print(
        "Regras aplicadas:",
        resumo["aplicadas"]
    )

    print(
        "Regras pendentes:",
        resumo["pendentes"]
    )

    print()
    print("===== DIAGNÓSTICO =====")
    print()

    for item in resumo["diagnostico"]:

        print(
            item["alvo"],
            "|",
            item["tipo"],
            "|",
            item["valor"],
            "|",
            item["status"],
            "|",
            item["restricoes_criadas"],
        )


if __name__ == "__main__":
    main()