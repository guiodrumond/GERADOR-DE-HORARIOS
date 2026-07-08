from src.domain.database import BaseDados


class BaseDadosValidator:
    """
    Valida integridade mínima da base carregada.

    Esta classe não resolve conflitos de horário.
    Ela apenas verifica se os dados básicos fazem sentido.
    """

    def __init__(self, base: BaseDados) -> None:
        self.base = base
        self.erros: list[str] = []

    def validate(self) -> None:
        self._validar_cursos()
        self._validar_turmas()
        self._validar_especialidades()
        self._validar_pares_pedagogicos()
        self._validar_atribuicoes()
        self._validar_slots()

        if self.erros:
            mensagem = "\n".join(self.erros)
            raise ValueError(f"Erros de validação encontrados:\n{mensagem}")

    def _validar_cursos(self) -> None:
        codigos = [curso.codigo for curso in self.base.cursos]

        self._validar_duplicados(
            valores=codigos,
            contexto="CURSOS.Curso",
        )

        for curso in self.base.cursos:
            if not curso.codigo:
                self.erros.append("Curso sem código encontrado na aba CURSOS.")

            if not curso.padrao_ftp:
                self.erros.append(
                    f"Curso {curso.codigo} sem Padrao_FTP definido."
                )

    def _validar_turmas(self) -> None:
        cursos_existentes = {curso.codigo for curso in self.base.cursos}
        turmas = [turma.codigo for turma in self.base.turmas]

        self._validar_duplicados(
            valores=turmas,
            contexto="TURMAS.Turma",
        )

        for turma in self.base.turmas:
            if not turma.codigo:
                self.erros.append("Turma sem código encontrada na aba TURMAS.")

            if turma.curso not in cursos_existentes:
                self.erros.append(
                    f"Turma {turma.codigo} referencia curso inexistente: {turma.curso}."
                )

    def _validar_especialidades(self) -> None:
        siglas = [especialidade.sigla for especialidade in self.base.especialidades]

        self._validar_duplicados(
            valores=siglas,
            contexto="ESPECIALIDADES_1ANO.Sigla",
        )

        for especialidade in self.base.especialidades:
            if not especialidade.sigla:
                self.erros.append(
                    "Especialidade sem sigla encontrada na aba ESPECIALIDADES_1ANO."
                )

            if especialidade.aulas <= 0:
                self.erros.append(
                    f"Especialidade {especialidade.sigla} possui carga inválida: {especialidade.aulas}."
                )

    def _validar_pares_pedagogicos(self) -> None:
        especialidades_existentes = {
            especialidade.sigla for especialidade in self.base.especialidades
        }

        for par in self.base.pares_pedagogicos:
            if par.especialidade_1 not in especialidades_existentes:
                self.erros.append(
                    f"Par pedagógico {par.codigo} referencia especialidade inexistente: {par.especialidade_1}."
                )

            if par.especialidade_2 not in especialidades_existentes:
                self.erros.append(
                    f"Par pedagógico {par.codigo} referencia especialidade inexistente: {par.especialidade_2}."
                )

    def _validar_atribuicoes(self) -> None:
        turmas_existentes = {turma.codigo for turma in self.base.turmas}
        professores_existentes = {
            professor.nome for professor in self.base.professores
        }
        especialidades_existentes = {
            especialidade.sigla for especialidade in self.base.especialidades
        }

        for atribuicao in self.base.atribuicoes:
            if atribuicao.turma not in turmas_existentes:
                self.erros.append(
                    f"Atribuição referencia turma inexistente: {atribuicao.turma}."
                )

            if atribuicao.professor not in professores_existentes:
                self.erros.append(
                    f"Atribuição referencia professor inexistente: {atribuicao.professor}."
                )

            if atribuicao.especialidade not in especialidades_existentes:
                self.erros.append(
                    f"Atribuição referencia especialidade inexistente: {atribuicao.especialidade}."
                )

    def _validar_slots(self) -> None:
        combinacoes = set()

        for slot in self.base.slots:
            chave = (slot.dia, slot.aula)

            if chave in combinacoes:
                self.erros.append(
                    f"Slot duplicado encontrado: {slot.dia} aula {slot.aula}."
                )

            combinacoes.add(chave)

            if not slot.dia:
                self.erros.append("Slot sem dia encontrado.")

            if slot.aula <= 0:
                self.erros.append(
                    f"Slot com aula inválida encontrado: {slot.dia} aula {slot.aula}."
                )

    def _validar_duplicados(self, valores: list[str], contexto: str) -> None:
        vistos = set()

        for valor in valores:
            if not valor:
                continue

            if valor in vistos:
                self.erros.append(
                    f"Valor duplicado em {contexto}: {valor}."
                )

            vistos.add(valor)