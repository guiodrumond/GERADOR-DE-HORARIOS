from ortools.sat.python import cp_model
import logging

class Scheduler:
    def __init__(self, model, config=None):
        self.model = model
        self.config = config or {}

    def solve(self):
        solver = cp_model.CpSolver()
        
        # Puxa os dados da aba CONFIG (com fallbacks de segurança caso algo falhe)
        max_time = int(self.config.get("MAX_TIME_SECONDS", 1800))
        num_workers = int(self.config.get("NUM_WORKERS", 16))
        random_seed = int(self.config.get("RANDOM_SEED", 42))

        # Aplica no motor do Google CP-SAT
        solver.parameters.max_time_in_seconds = max_time
        solver.parameters.num_search_workers = num_workers
        solver.parameters.random_seed = random_seed
        
        logging.info(f"⚙️ Configuração do Solver -> TEMPO MÁX: {max_time}s | WORKERS: {num_workers} | SEED: {random_seed}")

        status = solver.Solve(self.model)
        return solver, status