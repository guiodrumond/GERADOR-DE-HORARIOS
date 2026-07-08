class SolverStats:

    def __init__(
        self,
        base,
        variables,
        resumo_regras,
        total_block_assignment,
        total_turma_conflicts,
        total_professor_conflicts=0,
    ):

        self.base = base
        self.variables = variables

        self.resumo_regras = resumo_regras

        self.total_block_assignment = (
            total_block_assignment
        )

        self.total_turma_conflicts = (
            total_turma_conflicts
        )

        self.total_professor_conflicts = (
            total_professor_conflicts
        )

    def total_variaveis(self):

        total = 0

        for bloco_id in self.variables:

            total += len(
                self.variables[bloco_id]
            )

        return total

    def total_constraints_base(self):

        return (
            self.total_block_assignment
            + self.total_turma_conflicts
            + self.total_professor_conflicts
        )

    def total_constraints_engine(self):

        return (
            self.resumo_regras[
                "aplicadas"
            ]
        )

    def total_constraints(self):

        return (
            self.total_constraints_base()
            + self.total_constraints_engine()
        )

    def resumo(self):

        return {

            "turmas":
                len(
                    self.base.turmas
                ),

            "blocos":
                len(
                    self.base.blocos
                ),

            "slots":
                len(
                    self.base.slots
                ),

            "variaveis":
                self.total_variaveis(),

            "constraints_base":
                self.total_constraints_base(),

            "constraints_engine":
                self.total_constraints_engine(),

            "constraints_total":
                self.total_constraints(),

            "regras_aplicadas":
                self.resumo_regras[
                    "aplicadas"
                ],

            "regras_pendentes":
                self.resumo_regras[
                    "pendentes"
                ],

            "professor_conflicts":
                self.total_professor_conflicts,
        }

    def imprimir(self):

        dados = self.resumo()

        print()
        print(
            "===== ESTATÍSTICAS ====="
        )
        print()

        print(
            "Turmas:",
            dados["turmas"]
        )

        print(
            "Blocos:",
            dados["blocos"]
        )

        print(
            "Slots:",
            dados["slots"]
        )

        print()

        print(
            "Variáveis:",
            dados["variaveis"]
        )

        print()

        print(
            "Constraints Base:",
            dados[
                "constraints_base"
            ]
        )

        print(
            "Constraints Engine:",
            dados[
                "constraints_engine"
            ]
        )

        print(
            "Constraints Totais:",
            dados[
                "constraints_total"
            ]
        )

        print()

        print(
            "Regras Aplicadas:",
            dados[
                "regras_aplicadas"
            ]
        )

        print(
            "Regras Pendentes:",
            dados[
                "regras_pendentes"
            ]
        )

        print(
            "Professor Conflict:",
            dados[
                "professor_conflicts"
            ]
        )