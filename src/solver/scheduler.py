from ortools.sat.python import cp_model


class Scheduler:

    def __init__(self, model):

        self.model = model

    def solve(self):

        solver = cp_model.CpSolver()

        status = solver.Solve(
            self.model
        )

        return solver, status