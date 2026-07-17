from src.domain.database import BaseDados

class BaseDadosValidator:

    def __init__(self, base: BaseDados) -> None:
        self.base = base
        self.erros: list[str] = []

    def validate(self) -> None:
        self._validar_cursos()
        self._validar_turmas()
        self._validar_especialidades() # <-- CORRIGIDO: Retornou para o lugar certo
        self._validar_pares_pedagogicos()
        self._validar_atribuicoes()
        self._validar_slots()

        if self.erros:
            mensagem = "\n- ".join([""] + self.erros)
            raise ValueError(f"Erros de validação na base de dados (Planilha):{mensagem}")

    def _validar_cursos(self) -> None:
        codigos = [curso.codigo for curso in self.base.cursos if curso.codigo]
        self._validar_duplicados(valores=codigos, contexto="CURSOS.Curso")

        for curso in self.base.cursos:
            if not curso.codigo:
                self.erros.append("Curso sem código (Nome) encontrado na aba CURSOS.")
            if not curso.padrao_ftp:
                self.erros.append(f"Curso '{curso.codigo}' sem Padrao_FTP definido.")

    def _validar_turmas(self) -> None:
        cursos_existentes = {curso.codigo for curso in self.base.cursos}
        turmas = [turma.codigo for turma in self.base.turmas if turma.codigo]
        
        self._validar_duplicados(valores=turmas, contexto="TURMAS.Turma")

        for turma in self.base.turmas:
            if not turma.codigo:
                self.erros.append("Turma em branco encontrada na aba TURMAS.")
            if turma.curso not in cursos_existentes:
                self.erros.append(f"Turma '{turma.codigo}' referencia um curso inexistente: '{turma.curso}'.")

    def _validar_especialidades(self) -> None:
        # CORRIGIDO: Agora checa a combinação Ano + Sigla!
        chaves_ano_sigla = [(esp.ano, esp.sigla) for esp in self.base.especialidades if esp.sigla]
        self._validar_duplicados(valores=chaves_ano_sigla, contexto="ESPECIALIDADES (Ano + Sigla)")

        for esp in self.base.especialidades:
            if not esp.sigla:
                self.erros.append("Especialidade sem sigla encontrada na aba ESPECIALIDADES.")
            if esp.aulas <= 0:
                self.erros.append(f"Especialidade '{esp.sigla}' possui carga horária inválida: {esp.aulas} aulas.")

    def _validar_pares_pedagogicos(self) -> None:
        especialidades_existentes = {esp.sigla for esp in self.base.especialidades}

        for par in self.base.pares_pedagogicos:
            if par.especialidade_1 not in especialidades_existentes:
                self.erros.append(f"Par pedagógico '{par.codigo}' referencia especialidade_1 inexistente: '{par.especialidade_1}'.")
            if par.especialidade_2 not in especialidades_existentes:
                self.erros.append(f"Par pedagógico '{par.codigo}' referencia especialidade_2 inexistente: '{par.especialidade_2}'.")

    def _validar_atribuicoes(self) -> None:
        turmas_existentes = {turma.codigo for turma in self.base.turmas}
        especialidades_existentes = {esp.sigla for esp in self.base.especialidades}
        
        has_lista_professores = hasattr(self.base, 'professores') and bool(self.base.professores)
        if has_lista_professores:
            professores_existentes = {p.nome if hasattr(p, 'nome') else str(p) for p in self.base.professores}

        for atr in self.base.atribuicoes:
            # Valida professor
            if not atr.professor:
                self.erros.append(f"Atribuição encontrada sem professor na turma '{atr.turma}'.")
            elif has_lista_professores and atr.professor not in professores_existentes:
                self.erros.append(f"Atribuição referencia professor inexistente: '{atr.professor}'.")

            # Valida Turma e Especialidade
            if atr.turma not in turmas_existentes:
                self.erros.append(f"Atribuição referencia turma inexistente: '{atr.turma}'.")
            if atr.especialidade not in especialidades_existentes:
                self.erros.append(f"Atribuição referencia especialidade inexistente: '{atr.especialidade}' (Turma {atr.turma}).")

    def _validar_slots(self) -> None:
        combinacoes = set()

        for slot in self.base.slots:
            chave = (slot.dia, slot.aula)

            if chave in combinacoes:
                self.erros.append(f"Slot duplicado encontrado: Dia '{slot.dia}', Aula '{slot.aula}'.")
            combinacoes.add(chave)

            if not slot.dia:
                self.erros.append("Slot sem dia da semana encontrado.")
            if slot.aula <= 0:
                self.erros.append(f"Slot com número de aula inválido encontrado: Dia '{slot.dia}', Aula '{slot.aula}'.")

    # CORRIGIDO: Recuo de indentação (alinhado com as outras funções)
    def _validar_duplicados(self, valores: list, contexto: str) -> None:
        chaves_vistas = set()
        for v in valores:
            if v in chaves_vistas:
                self.erros.append(f"Valor duplicado em {contexto}: '{v}'.")
            chaves_vistas.add(v)