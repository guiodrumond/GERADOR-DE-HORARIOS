from src.data.loader import ExcelLoader

from src.builder.pedagogical_blocks import (
    PedagogicalBlockBuilder
)

ARQUIVO = "excel/GERADOR_DE_HORARIOS.xlsx"


def main():

    loader = ExcelLoader(ARQUIVO)

    base = loader.load()

    builder = PedagogicalBlockBuilder(base)

    base.blocos = builder.build()

    print()
    print("===== ÚLTIMOS SLOTS =====")
    print()
    print(len(base.slots))

if __name__ == "__main__":
    main()