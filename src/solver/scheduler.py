from ortools.sat.python import cp_model


class Scheduler:

    def __init__(self, model):

        self.model = model

    def solve(self):

        solver = cp_model.CpSolver()

        solver.parameters.max_time_in_seconds = 30

        status = solver.Solve(
            self.model
        )

        return solver, status