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
    print("===== MATEMÁTICA =====")
    print()

    for bloco in base.blocos:

        if "_MAT_" in bloco.id:

            print(bloco.id)

if __name__ == "__main__":
    main()