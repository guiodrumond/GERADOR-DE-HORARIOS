from collections import Counter

from src.data.loader import ExcelLoader
from src.builder.pedagogical_blocks import (
    PedagogicalBlockBuilder
)

ARQUIVO = "excel/GERADOR_DE_HORARIOS.xlsx"


def main():

    print()
    print("===== CARREGANDO BASE =====")
    print()

    loader = ExcelLoader(ARQUIVO)

    base = loader.load()

    builder = PedagogicalBlockBuilder(base)

    base.blocos = builder.build()

    print("CONFIG :", len(base.config))
    print("CURSOS :", len(base.cursos))
    print("TURMAS :", len(base.turmas))
    print("ESPECIALIDADES :", len(base.especialidades))
    print("PARES :", len(base.pares_pedagogicos))
    print("PADROES :", len(base.padroes_pedagogicos))

    print()
    print("===== PARES PEDAGÓGICOS =====")
    print()

    for par in base.pares_pedagogicos:

        print(
            par.codigo,
            par.especialidade_1,
            "+",
            par.especialidade_2
        )

    print()
    print("===== BLOCOS DE PARES =====")
    print()

    for bloco in base.blocos:

        if len(bloco.componentes) > 1:

            print(
                bloco.id,
                bloco.componentes,
                bloco.tamanho
            )

    print()
    print("===== VERIFICAÇÃO =====")
    print()

    erros = 0

    for bloco in base.blocos:

        if bloco.componentes == ["HIS"]:
            erros += 1
            print("ERRO:", bloco.id)

        if bloco.componentes == ["SOC"]:
            erros += 1
            print("ERRO:", bloco.id)

        if bloco.componentes == ["ART"]:
            erros += 1
            print("ERRO:", bloco.id)

        if bloco.componentes == ["ING"]:
            erros += 1
            print("ERRO:", bloco.id)

    if erros == 0:
        print("OK - Nenhum componente de par foi criado isoladamente.")

    pares = 0

    for bloco in base.blocos:

        if len(bloco.componentes) > 1:
            pares += 1

    print()
    print("Quantidade de blocos de pares:", pares)

    print()
    print("===== CONTAGEM DE PARES =====")
    print()

    contador = Counter()

    for bloco in base.blocos:

        if len(bloco.componentes) > 1:

            chave = tuple(
                sorted(bloco.componentes)
            )

            contador[chave] += 1

    for chave, qtd in contador.items():

        print(
            chave,
            "->",
            qtd
        )

    print()
    print("===== PRIMEIROS 10 BLOCOS =====")
    print()

    for bloco in base.blocos[:10]:
        print(bloco)


    print()
    print("===== IDS DOS PARES =====")
    print()

    for bloco in base.blocos:

        if bloco.componentes == ["HIS", "SOC"]:

            print(bloco.id)

if __name__ == "__main__":
    main()