class ObjectiveBuilder:

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

    def add_term(
        self,
        expression,
        peso: int = 1,
        descricao: str = "",
    ):

        self.terms.append(
            expression * peso
        )

        if descricao:

            self.diagnostico.append(
                {
                    "descricao": descricao,
                    "peso": peso,
                }
            )

    def add_expression(
        self,
        expression,
        descricao: str = "",
    ):

        self.terms.append(
            expression
        )

        if descricao:

            self.diagnostico.append(
                {
                    "descricao": descricao,
                    "peso": "EXP",
                }
            )

    def add_terms(
        self,
        terms,
        peso: int = 1,
        descricao: str = "",
    ):

        for expression in terms:

            self.add_term(
                expression=expression,
                peso=peso,
                descricao=descricao,
            )

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