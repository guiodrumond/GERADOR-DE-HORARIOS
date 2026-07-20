from pathlib import Path
from openpyxl import Workbook
from src.export.excel_styles import ExcelStyles

class ExcelExporter:
    # Removemos o planning_result antigo que não tem mais utilidade!
    def __init__(self, base):
        self.base = base
        
        # Mapas auxiliares para cruzar siglas, áreas e professores
        self.componente_para_grupo = self._criar_mapa_componente_grupo()
        self.professores_por_area = self._criar_mapa_professores_por_area()

    def export(self, grid, caminho_saida: str):
        caminho = Path(caminho_saida)
        caminho.parent.mkdir(parents=True, exist_ok=True)

        workbook = Workbook()
        aba_padrao = workbook.active
        workbook.remove(aba_padrao)

        sheet_turmas = workbook.create_sheet(title="TURMAS")
        self._write_turmas_sheet(sheet=sheet_turmas, grid=grid)

        sheet_professores = workbook.create_sheet(title="PROFESSORES")
        self._write_professores_sheet(sheet=sheet_professores, grid=grid)

        workbook.save(caminho)
        return caminho

    def _write_turmas_sheet(self, sheet, grid):
        dias = self._dias()
        aulas = self._aulas()
        self._setup_general_sheet(sheet)

        current_row = 1
        for turma in self._turmas_ativas():
            current_row = self._write_turma_table(
                sheet=sheet,
                grid=grid,
                turma=turma.codigo,
                dias=dias,
                aulas=aulas,
                start_row=current_row,
            )
            current_row += 2

    def _write_professores_sheet(self, sheet, grid):
        dias = self._dias()
        aulas = self._aulas()
        self._setup_general_sheet(sheet)

        professores = self._professores_do_grid(grid)
        current_row = 1

        for professor in professores:
            current_row = self._write_professor_table(
                sheet=sheet,
                grid=grid,
                professor=professor,
                dias=dias,
                aulas=aulas,
                start_row=current_row,
            )
            current_row += 2

    def _write_turma_table(self, sheet, grid, turma, dias, aulas, start_row):
        total_colunas = len(dias) + 1

        sheet.merge_cells(
            start_row=start_row, start_column=1, end_row=start_row, end_column=total_colunas
        )
        
        title_cell = sheet.cell(row=start_row, column=1, value=f"HORÁRIO {turma}")
        ExcelStyles.apply_title(title_cell)
        sheet.row_dimensions[start_row].height = 28

        header_row = start_row + 1
        self._write_header(sheet=sheet, dias=dias, row=header_row)

        body_start = start_row + 2

        for row_offset, aula in enumerate(aulas):
            row = body_start + row_offset
            
            aula_cell = sheet.cell(row=row, column=1, value=aula)
            ExcelStyles.apply_aula_cell(aula_cell)
            sheet.row_dimensions[row].height = 45

            for col_offset, dia in enumerate(dias, start=2):
                cell_data = grid.get(turma, dia, aula)
                texto = ""
                grupo = None

                if cell_data:
                    componente = cell_data.texto
                    professor = cell_data.professor
                    grupo = self.componente_para_grupo.get(componente.upper())

                    if professor:
                        texto = f"{componente}\n{professor}"
                    else:
                        texto = componente

                cell = sheet.cell(row=row, column=col_offset, value=texto)
                ExcelStyles.apply_body(cell, texto, grupo)

        self._merge_blocos_turma(
            sheet=sheet,
            grid=grid,
            turma=turma,
            dias=dias,
            aulas=aulas,
            body_start=body_start,
        )

        return body_start + len(aulas)

    def _write_professor_table(self, sheet, grid, professor, dias, aulas, start_row):
        total_colunas = len(dias) + 1

        sheet.merge_cells(
            start_row=start_row, start_column=1, end_row=start_row, end_column=total_colunas
        )
        
        title_cell = sheet.cell(row=start_row, column=1, value=professor)
        ExcelStyles.apply_title(title_cell)
        sheet.row_dimensions[start_row].height = 28

        header_row = start_row + 1
        self._write_header(sheet=sheet, dias=dias, row=header_row)

        body_start = start_row + 2

        for row_offset, aula in enumerate(aulas):
            row = body_start + row_offset
            
            aula_cell = sheet.cell(row=row, column=1, value=aula)
            ExcelStyles.apply_aula_cell(aula_cell)
            sheet.row_dimensions[row].height = 45

            for col_offset, dia in enumerate(dias, start=2):
                # O novo _entradas_professor_slot agora avisa se achou um planejamento!
                entradas, is_planning = self._entradas_professor_slot(
                    grid=grid, professor=professor, dia=dia, aula=aula
                )

                if is_planning:
                    # Tira duplicatas por segurança e força o grupo para "PLANEJAMENTO"
                    texto = "\n".join(list(dict.fromkeys(entradas))) 
                    grupo = "PLANEJAMENTO"
                elif entradas:
                    texto = "\n".join(entradas)
                    componente = entradas[0].split(" - ")[-1].strip()
                    grupo = self.componente_para_grupo.get(componente.upper())
                else:
                    texto = ""
                    grupo = None

                cell = sheet.cell(row=row, column=col_offset, value=texto)
                ExcelStyles.apply_body(cell, texto, grupo)

        return body_start + len(aulas)

    def _write_header(self, sheet, dias, row):
        cell = sheet.cell(row=row, column=1, value="AULA")
        ExcelStyles.apply_header(cell)

        for coluna, dia in enumerate(dias, start=2):
            cell = sheet.cell(row=row, column=coluna, value=dia)
            ExcelStyles.apply_header(cell)

    def _merge_blocos_turma(self, sheet, grid, turma, dias, aulas, body_start):
        for col_offset, dia in enumerate(dias, start=2):
            inicio = None
            chave_atual = None

            for index, aula in enumerate(aulas):
                row = body_start + index
                cell_data = grid.get(turma, dia, aula)

                chave_merge = (
                    (cell_data.bloco_id, cell_data.texto, cell_data.professor)
                    if cell_data else None
                )

                if chave_merge is not None and chave_merge == chave_atual:
                    continue

                if chave_atual is not None and inicio is not None and row - inicio > 1:
                    self._merge_range(sheet, inicio, row - 1, col_offset)

                inicio = row
                chave_atual = chave_merge

            ultima_row = body_start + len(aulas) - 1
            if chave_atual is not None and inicio is not None and ultima_row - inicio >= 1:
                self._merge_range(sheet, inicio, ultima_row, col_offset)

    def _merge_range(self, sheet, start_row, end_row, column):
        sheet.merge_cells(
            start_row=start_row, start_column=column, end_row=end_row, end_column=column
        )

    def _entradas_professor_slot(self, grid, professor, dia, aula):
        entradas = []
        is_planning = False
        
        for turma in grid.turmas():
            cell = grid.get(turma, dia, aula)
            if not cell or cell.professor != professor:
                continue
                
            # SE FOR PLANEJAMENTO, processa de forma inteligente
            if cell.bloco_id == "PLANEJAMENTO":
                entradas.append(cell.texto)
                is_planning = True
            else:
                entradas.append(f"{turma} - {cell.texto}")
                
        return entradas, is_planning

    def _professores_do_grid(self, grid):
        professores = set()
        for turma in grid.turmas():
            for dia in self._dias():
                for aula in self._aulas():
                    cell = grid.get(turma, dia, aula)
                    if cell and cell.professor:
                        professores.add(cell.professor)
        return sorted(professores)

    def _setup_general_sheet(self, sheet):
        sheet.sheet_view.showGridLines = False
        sheet.column_dimensions["A"].width = 10
        
        dias = self._dias()
        for col in range(2, len(dias) + 2):
            letter = sheet.cell(row=1, column=col).column_letter
            sheet.column_dimensions[letter].width = 25

    def _turmas_ativas(self):
        return [turma for turma in self.base.turmas if turma.ativa]

    def _dias(self):
        dias = []
        for slot in self.base.slots:
            if slot.dia not in dias:
                dias.append(slot.dia)
        return dias

    def _aulas(self):
        return sorted({slot.aula for slot in self.base.slots})

    def _criar_mapa_componente_grupo(self):
        mapa = {}
        for esp in self.base.especialidades:
            mapa[esp.sigla.upper()] = esp.componente.upper()
        return mapa

    def _criar_mapa_professores_por_area(self):
        """Mapeia dinamicamente quais professores pertencem a qual área (ex: MEST, LEST)"""
        mapa = {}
        for atribuicao in self.base.atribuicoes:
            if not atribuicao.professor:
                continue
            
            sigla = atribuicao.especialidade.upper()
            area = self.componente_para_grupo.get(sigla)
            
            if area:
                if area not in mapa:
                    mapa[area] = set()
                mapa[area].add(atribuicao.professor)
                
        return {area: list(profs) for area, profs in mapa.items()}