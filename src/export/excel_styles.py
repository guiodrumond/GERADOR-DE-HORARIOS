from openpyxl.styles import (
    Alignment,
    Border,
    Font,
    PatternFill,
    Side,
)


class ExcelStyles:
    """
    Centraliza os estilos usados na exportação Excel.

    Esta classe não conhece regra de negócio.
    Apenas aplica aparência visual às planilhas.
    """

    TITLE_FILL = "1F4E78"
    HEADER_FILL = "D9EAF7"
    EMPTY_FILL = "F2F2F2"
    BORDER_COLOR = "BFBFBF"

    COMPONENT_COLORS = {
        "PROJ": "F4B183",
        "FTP": "FFD966",
        "MAT": "A9D18E",
        "POR": "9DC3E6",
        "EDF": "D9EAD3",
        "ART": "EADCF8",
        "ING": "EADCF8",
        "ART/ING": "EADCF8",
        "HIS": "FCE4D6",
        "SOC": "FCE4D6",
        "HIS/SOC": "FCE4D6",
        "GEO": "FCE4D6",
        "FIL": "FCE4D6",
        "FIS": "DDEBF7",
        "QUI": "DDEBF7",
        "BIO": "DDEBF7",
    }

    @classmethod
    def thin_border(cls):

        side = Side(
            style="thin",
            color=cls.BORDER_COLOR,
        )

        return Border(
            left=side,
            right=side,
            top=side,
            bottom=side,
        )

    @classmethod
    def title_fill(cls):

        return PatternFill(
            fill_type="solid",
            fgColor=cls.TITLE_FILL,
        )

    @classmethod
    def header_fill(cls):

        return PatternFill(
            fill_type="solid",
            fgColor=cls.HEADER_FILL,
        )

    @classmethod
    def empty_fill(cls):

        return PatternFill(
            fill_type="solid",
            fgColor=cls.EMPTY_FILL,
        )

    @classmethod
    def component_fill(cls, texto: str):

        cor = cls._cor_componente(
            texto
        )

        return PatternFill(
            fill_type="solid",
            fgColor=cor,
        )

    @classmethod
    def _cor_componente(cls, texto: str):

        if not texto:
            return cls.EMPTY_FILL

        texto = texto.strip().upper()

        if texto in cls.COMPONENT_COLORS:
            return cls.COMPONENT_COLORS[texto]

        primeiro = texto.split("/")[0]

        return cls.COMPONENT_COLORS.get(
            primeiro,
            "FFFFFF",
        )

    @classmethod
    def apply_title(
        cls,
        cell,
    ):

        cell.font = Font(
            bold=True,
            color="FFFFFF",
            size=14,
        )

        cell.fill = cls.title_fill()

        cell.alignment = Alignment(
            horizontal="center",
            vertical="center",
        )

    @classmethod
    def apply_header(
        cls,
        cell,
    ):

        cell.font = Font(
            bold=True,
            color="000000",
        )

        cell.fill = cls.header_fill()

        cell.alignment = Alignment(
            horizontal="center",
            vertical="center",
        )

        cell.border = cls.thin_border()

    @classmethod
    def apply_body(
        cls,
        cell,
        texto: str,
    ):

        cell.font = Font(
            bold=False,
            color="000000",
        )

        cell.alignment = Alignment(
            horizontal="center",
            vertical="center",
            wrap_text=True,
        )

        cell.border = cls.thin_border()

        if texto:

            cell.fill = cls.component_fill(
                texto
            )

        else:

            cell.fill = cls.empty_fill()

    @classmethod
    def apply_aula_cell(
        cls,
        cell,
    ):

        cell.font = Font(
            bold=True,
            color="000000",
        )

        cell.fill = cls.header_fill()

        cell.alignment = Alignment(
            horizontal="center",
            vertical="center",
        )

        cell.border = cls.thin_border()