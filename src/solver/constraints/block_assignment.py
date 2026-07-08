class BlockAssignmentConstraint:

    def __init__(
        self,
        model,
        variables,
    ):

        self.model = model
        self.variables = variables

    def build(self):

        quantidade = 0

        for bloco_id, slots in self.variables.items():

            self.model.Add(
                sum(
                    slots.values()
                ) == 1
            )

            quantidade += 1

        return quantidade