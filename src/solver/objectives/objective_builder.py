class ObjectiveBuilder:
    """
    Constrói a função objetivo do modelo CP-SAT.

    Nesta primeira versão, ele apenas fornece a infraestrutura:
    - registrar termos de pontuação
    - armazenar diagnóstico
    - aplicar model.Maximize(...)

    Os objetivos reais serão adicionados em handlers específicos.
    """

    def __init__(
        self,
        model,
        variables,
        base,
        regras,
    ):

        self.model = model
        self.variables = variables
        self.base = base
        self.regras = regras

        self.terms = []
        self.diagnostico = []

    # ==================================================
    # ADICIONAR TERMOS
    # ==================================================

    def add_term(
        self,
        expression,
        peso: int,
        descricao: str,
    ):

        self.terms.append(
            expression * peso
        )

        self.diagnostico.append(
            {
                "descricao": descricao,
                "peso": peso,
            }
        )

    def add_terms(
        self,
        terms,
        peso: int,
        descricao: str,
    ):

        for expression in terms:

            self.add_term(
                expression=expression,
                peso=peso,
                descricao=descricao,
            )

    # ==================================================
    # BUILD
    # ==================================================

    def build(self):

        if not self.terms:

            return 0

        self.model.Maximize(
            sum(
                self.terms
            )
        )

        return len(
            self.terms
        )

    # ==================================================
    # RESUMO
    # ==================================================

    def resumo(self):

        return {
            "termos": len(
                self.terms
            ),
            "diagnostico": self.diagnostico,
        }

    def imprimir_resumo(self):

        resumo = self.resumo()

        print()
        print("===== OBJETIVO =====")
        print()

        print(
            "Termos de objetivo:",
            resumo["termos"]
        )

        if not resumo["diagnostico"]:

            print(
                "Nenhum objetivo aplicado."
            )

            return

        print()

        for item in resumo["diagnostico"][:20]:

            print(
                item["descricao"],
                "| peso:",
                item["peso"],
            )