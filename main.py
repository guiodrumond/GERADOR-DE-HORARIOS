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

    print()
    print("===== PADRÕES PEDAGÓGICOS =====")
    print()

    for padrao in base.padroes_pedagogicos:

        print(
            padrao.componente,
            "|",
            padrao.tipo,
            "|",
            padrao.valor
        )

        print()
        print("===== FTP =====")
        print()

        for bloco in base.blocos:

            if "FTP" in bloco.id:

                print(
                    bloco.id,
                    bloco.tamanho
                )

if __name__ == "__main__":
    main()