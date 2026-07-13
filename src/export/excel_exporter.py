from pathlib import Path

from openpyxl import Workbook

from src.export.excel_styles import (
    ExcelStyles,
)


class ExcelExporter:

    def __init__(
        self,
        base,
    ):

        self.base = base

        self.componente_para_area = (
            self._criar_mapa_componente_area()
            )

    # ==================================================
    # EXPORTAÇÃO
    # ==================================================

    def export(
        self,
        grid,
        caminho_saida: str,
    ):

        caminho = Path(
            caminho_saida
        )

        caminho.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        workbook = Workbook()

        aba_padrao = workbook.active

        workbook.remove(
            aba_padrao
        )

        for turma in self._turmas_ativas():

            sheet = workbook.create_sheet(
                title=self._safe_sheet_name(
                    turma.codigo
                )
            )

            self._write_sheet(
                sheet=sheet,
                grid=grid,
                turma=turma.codigo,
            )

        workbook.save(
            caminho
        )

        return caminho

    # ==================================================
    # TURMAS
    # ==================================================

    def _turmas_ativas(self):

        return [
            turma
            for turma in self.base.turmas
            if turma.ativa
        ]

    # ==================================================
    # PLANILHA
    # ==================================================

    def _write_sheet(
        self,
        sheet,
        grid,
        turma,
    ):

        dias = self._dias()
        aulas = self._aulas()

        self._setup_sheet(
            sheet,
            turma,
            dias,
        )

        self._write_header(
            sheet,
            dias,
        )

        self._write_body(
            sheet,
            grid,
            turma,
            dias,
            aulas,
        )

        self._merge_blocos(
            sheet,
            grid,
            turma,
            dias,
            aulas,
        )

        self._write_summary(
            sheet,
            grid,
            turma,
            dias,
            aulas,
        )

    # ==================================================
    # LAYOUT
    # ==================================================

    def _setup_sheet(
        self,
        sheet,
        turma,
        dias,
    ):

        total_colunas = (
            len(dias)
            + 1
        )

        sheet.merge_cells(
            start_row=1,
            start_column=1,
            end_row=1,
            end_column=total_colunas,
        )

        title_cell = sheet.cell(
            row=1,
            column=1,
            value=f"HORÁRIO {turma}",
        )

        ExcelStyles.apply_title(
            title_cell
        )

        sheet.row_dimensions[
            1
        ].height = 28

        sheet.column_dimensions[
            "A"
        ].width = 10

        for col in range(
            2,
            total_colunas + 1,
        ):

            letter = sheet.cell(
                row=2,
                column=col,
            ).column_letter

            sheet.column_dimensions[
                letter
            ].width = 22

        sheet.sheet_view.showGridLines = False

    # ==================================================
    # CABEÇALHO
    # ==================================================

    def _write_header(
        self,
        sheet,
        dias,
    ):

        cell = sheet.cell(
            row=2,
            column=1,
            value="AULA",
        )

        ExcelStyles.apply_header(
            cell
        )

        for coluna, dia in enumerate(
            dias,
            start=2,
        ):

            cell = sheet.cell(
                row=2,
                column=coluna,
                value=dia,
            )

            ExcelStyles.apply_header(
                cell
            )

    # ==================================================
    # CORPO
    # ==================================================

    def _write_body(
        self,
        sheet,
        grid,
        turma,
        dias,
        aulas,
    ):

        linha_inicial = 3

        for row_offset, aula in enumerate(
            aulas
        ):

            row = (
                linha_inicial
                + row_offset
            )

            aula_cell = sheet.cell(
                row=row,
                column=1,
                value=aula,
            )

            ExcelStyles.apply_aula_cell(
                aula_cell
            )

            sheet.row_dimensions[
                row
            ].height = 45

            for col_offset, dia in enumerate(
                dias,
                start=2,
            ):

                cell_data = grid.get(
                    turma,
                    dia,
                    aula,
                )

                if cell_data:

                    componente = (
                        cell_data.texto
                    )

                    area = (
                        self.componente_para_area.get(
                            componente.upper()
                        )
                    )

                    professor = (
                        cell_data.professor
                    )

                    if professor:

                        texto = (
                            f"{componente}\n"
                            f"{professor}"
                        )

                    else:

                        texto = componente

                else:

                    texto = ""
                    area = None

                cell = sheet.cell(
                    row=row,
                    column=col_offset,
                    value=texto,
                )

                ExcelStyles.apply_body(
                    cell,
                    texto,
                    area,
                )

    # ==================================================
    # MESCLAGEM
    # ==================================================

    def _merge_blocos(
        self,
        sheet,
        grid,
        turma,
        dias,
        aulas,
    ):

        linha_inicial = 3

        for col_offset, dia in enumerate(
            dias,
            start=2,
        ):

            inicio = None
            chave_atual = None

            for index, aula in enumerate(
                aulas
            ):

                row = (
                    linha_inicial
                    + index
                )

                cell_data = grid.get(
                    turma,
                    dia,
                    aula,
                )

                if cell_data:

                    chave_merge = (
                        cell_data.bloco_id,
                        cell_data.texto,
                    )

                else:

                    chave_merge = None

                if (
                    chave_merge is not None
                    and chave_merge == chave_atual
                ):
                    continue

                if (
                    chave_atual is not None
                    and inicio is not None
                    and row - inicio > 1
                ):

                    self._merge_range(
                        sheet,
                        inicio,
                        row - 1,
                        col_offset,
                    )

                inicio = row
                chave_atual = chave_merge

            ultima_row = (
                linha_inicial
                + len(aulas)
                - 1
            )

            if (
                chave_atual is not None
                and inicio is not None
                and ultima_row - inicio >= 1
            ):

                self._merge_range(
                    sheet,
                    inicio,
                    ultima_row,
                    col_offset,
                )

    def _merge_range(
        self,
        sheet,
        start_row,
        end_row,
        column,
    ):

        sheet.merge_cells(
            start_row=start_row,
            start_column=column,
            end_row=end_row,
            end_column=column,
        )

    # ==================================================
    # RESUMO
    # ==================================================

    def _write_summary(
        self,
        sheet,
        grid,
        turma,
        dias,
        aulas,
    ):

        start_row = (
            len(aulas)
            + 5
        )

        total = 0

        for dia in dias:

            for aula in aulas:

                if grid.get(
                    turma,
                    dia,
                    aula,
                ):
                    total += 1

        label = sheet.cell(
            row=start_row,
            column=1,
            value="Aulas ocupadas",
        )

        value = sheet.cell(
            row=start_row,
            column=2,
            value=total,
        )

        ExcelStyles.apply_header(
            label
        )

        ExcelStyles.apply_body(
            value,
            str(total),
        )

    # ==================================================
    # SLOTS
    # ==================================================

    def _dias(self):

        dias = []

        for slot in self.base.slots:

            if slot.dia not in dias:

                dias.append(
                    slot.dia
                )

        return dias

    def _aulas(self):

        return sorted(
            {
                slot.aula
                for slot in self.base.slots
            }
        )

    # ==================================================
    # UTIL
    # ==================================================

    def _safe_sheet_name(
        self,
        name: str,
    ):

        invalidos = [
            "\\",
            "/",
            "*",
            "?",
            ":",
            "[",
            "]",
        ]

        result = name

        for char in invalidos:

            result = result.replace(
                char,
                "_",
            )

        return result[:31]

    def _criar_mapa_componente_area(
        self,
    ):

        mapa = {}

        for esp in self.base.especialidades:

            mapa[
                esp.sigla.upper()
            ] = esp.componente.upper()

        return mapa