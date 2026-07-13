from openpyxl.styles import (
    Alignment,
    Border,
    Font,
    PatternFill,
    Side,
)


class ExcelStyles:

    TITLE_FILL = "1F4E78"
    HEADER_FILL = "D9EAF7"
    EMPTY_FILL = "F2F2F2"
    BORDER_COLOR = "BFBFBF"

    AREA_COLORS = {
        "CHSA": "FCE4D6",
        "CNST": "DDEBF7",
        "LEST": "EADCF8",
        "MEST": "A9D18E",
        "FTP": "FFD966",
        "PROJ": "F4B183",
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
    def area_fill(
        cls,
        area,
    ):

        if not area:

            cor = cls.EMPTY_FILL

        else:

            cor = cls.AREA_COLORS.get(
                area.upper(),
                "FFFFFF",
            )

        return PatternFill(
            fill_type="solid",
            fgColor=cor,
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
        texto,
        area=None,
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

            cell.fill = cls.area_fill(
                area
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