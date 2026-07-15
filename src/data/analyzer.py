from collections import defaultdict
import logging

class PedagogicalPairsAnalyzer:
    """
    Analisa a atribuição de professores antes de rodar o Solver.
    Detecta quais turmas podem fazer o espelhamento em 'X' (Pares Perfeitos)
    e quais não podem devido a incompatibilidades de professores (Assimétricos).
    """

    def __init__(self, base):
        self.base = base

    def analisar(self) -> dict:
        relatorio = {}

        # Mapeia atribuições: {(turma, especialidade): professor}
        atribuicoes_map = {
            (atr.turma, atr.especialidade.upper()): atr.professor
            for atr in self.base.atribuicoes
        }

        for par in self.base.pares_pedagogicos:
            c1 = par.especialidade_1.upper()
            c2 = par.especialidade_2.upper()
            chave_par = f"{c1} & {c2}"

            # Agrupa turmas que compartilham a mesma dupla de professores para este par
            grupos_professores = defaultdict(list)

            for turma_obj in self.base.turmas:
                if not turma_obj.ativa:
                    continue
                
                t_name = turma_obj.codigo
                prof_1 = atribuicoes_map.get((t_name, c1))
                prof_2 = atribuicoes_map.get((t_name, c2))

                if prof_1 and prof_2:
                    signature = tuple(sorted([prof_1, prof_2]))
                    grupos_professores[signature].append(t_name)

            pares_perfeitos = []
            turmas_assimetricas = []

            for signature, turmas in grupos_professores.items():
                # Agrupa de duas em duas turmas para formar o "X" perfeito
                while len(turmas) >= 2:
                    t1 = turmas.pop(0)
                    t2 = turmas.pop(0)
                    pares_perfeitos.append((t1, t2, signature[0], signature[1]))
                
                # Se sobrou uma turma sozinha com essa assinatura de professores
                if len(turmas) == 1:
                    turmas_assimetricas.append((turmas[0], signature[0], signature[1]))

            relatorio[chave_par] = {
                "perfeitos": pares_perfeitos,
                "assimetricos": turmas_assimetricas
            }

        return relatorio

    def imprimir_avisos_pre_solver(self, analise: dict):
        tem_avisos = False
        
        print("\n" + "="*80)
        print("=== AUDITORIA DE ATRIBUIÇÃO (PARES PEDAGÓGICOS) ===".center(80))
        print("="*80)

        for par_nome, dados in analise.items():
            assim = dados["assimetricos"]
            perf = dados["perfeitos"]
            
            print(f"\n>>> PAR: {par_nome}")
            print(f"  - Pares estruturalmente possíveis de espelhar em 'X': {len(perf)}")
            
            if assim:
                tem_avisos = True
                print("  [ATENÇÃO] Turmas impossibilitadas de fazer o 'X' por incompatibilidade de professores:")
                for t, p1, p2 in assim:
                    print(f"    * Turma '{t}': Usa os professores '{p1}' & '{p2}'.")
                    print("      Motivo: Nenhuma outra turma compartilha exatamente essa mesma dupla para este par.")
            else:
                print("  - Todas as turmas deste par possuem professores simétricos! Pronto para o Solver.")

        if tem_avisos:
            print("\n[RECOMENDAÇÃO]: Se deseja o 'X' para as turmas listadas acima, altere as atribuições")
            print("no Excel para que elas compartilhem a mesma dupla de professores de Artes e Inglês.")
        print("="*80 + "\n")