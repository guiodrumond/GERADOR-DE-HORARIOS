from dataclasses import dataclass


@dataclass
class GridCell:

    turma: str

    dia: str

    aula: int

    texto: str

    bloco_id: str | None = None

    professor: str | None = None


class Grid:

    def __init__(self):

        self.cells = {}

    # =====================================
    # ESCRITA
    # =====================================

    def set(
        self,
        turma: str,
        dia: str,
        aula: int,
        texto: str,
        bloco_id: str | None = None,
        professor: str | None = None,
    ):

        chave = (
            turma,
            dia,
            aula,
        )

        self.cells[chave] = GridCell(
            turma=turma,
            dia=dia,
            aula=aula,
            texto=texto,
            bloco_id=bloco_id,
            professor=professor,
        )

    # =====================================
    # LEITURA
    # =====================================

    def get(
        self,
        turma: str,
        dia: str,
        aula: int,
    ):

        return self.cells.get(
            (
                turma,
                dia,
                aula,
            )
        )

    def get_text(
        self,
        turma: str,
        dia: str,
        aula: int,
    ):

        cell = self.get(
            turma,
            dia,
            aula,
        )

        if cell is None:
            return ""

        return cell.texto

    def get_professor(
        self,
        turma: str,
        dia: str,
        aula: int,
    ):

        cell = self.get(
            turma,
            dia,
            aula,
        )

        if cell is None:
            return ""

        return cell.professor or ""

    # =====================================
    # TURMAS
    # =====================================

    def turmas(self):

        resultado = {
            turma
            for turma, _, _
            in self.cells.keys()
        }

        return sorted(resultado)

    # =====================================
    # ESTATÍSTICAS
    # =====================================

    def total_cells(self):

        return len(
            self.cells
        )

    # =====================================
    # DEBUG
    # =====================================

    def summary(self):

        professores = set()

        for cell in self.cells.values():

            if cell.professor:

                professores.add(
                    cell.professor
                )

        return {

            "turmas":
                len(self.turmas()),

            "cells":
                self.total_cells(),

            "professores":
                len(professores),
        }