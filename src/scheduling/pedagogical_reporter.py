class PedagogicalPairsReporter:
    """
    Gera o relatório final de pós-processamento.
    Mostra onde o 'X' aconteceu e avisa se algum par perfeito estrutural
    foi quebrado devido a restrições de horários.
    """

    def __init__(self, solver, variables, base, analise_previa):
        self.solver = solver
        self.variables = variables
        self.base = base
        self.analise_previa = analise_previa

    def print_report(self):
        print("\n" + "="*80)
        print("=== RELATÓRIO DE EXECUÇÃO DOS PARES PEDAGÓGICOS ===".center(80))
        print("="*80)

        for par in self.base.pares_pedagogicos:
            c1 = par.especialidade_1.upper()
            c2 = par.especialidade_2.upper()
            chave_par = f"{c1} & {c2}"
            
            print(f"\n>>> PAR: {chave_par}")
            
            # 1. Mapear onde cada aula foi parar na grade final
            alocacoes = {}  # {turma: {componente: (dia, aula)}}
            
            for bloco in self.base.blocos:
                if len(bloco.componentes) == 1:
                    comp = bloco.componentes[0].upper()
                    if comp in (c1, c2):
                        for slot_id, var in self.variables[bloco.id].items():
                            if self.solver.Value(var) == 1:
                                dia, aula = slot_id.split("_")
                                alocacoes.setdefault(bloco.turma, {})[comp] = (dia, int(aula))

            # 2. Verificar o status de cada par perfeito que foi planejado
            dados_analise = self.analise_previa.get(chave_par, {"perfeitos": [], "assimetricos": []})
            
            print("\n  [STATUS DO ESPELHAMENTO EM 'X']:")
            for t1, t2, p1, p2 in dados_analise["perfeitos"]:
                # Recupera os slots alocados pelo Solver
                slots_t1 = alocacoes.get(t1, {})
                slots_t2 = alocacoes.get(t2, {})

                t1_c1 = slots_t1.get(c1)
                t1_c2 = slots_t1.get(c2)
                t2_c1 = slots_t2.get(c1)
                t2_c2 = slots_t2.get(c2)

                # Verifica se estão no mesmo dia, slots consecutivos e invertidos (O "X")
                sucesso = False
                if t1_c1 and t1_c2 and t2_c1 and t2_c2:
                    dia_t1, aula_t1 = t1_c1
                    dia_t2, aula_t2 = t2_c1
                    
                    if (dia_t1 == dia_t2 and 
                        slots_t1[c2][0] == dia_t1 and slots_t2[c2][0] == dia_t1 and
                        abs(aula_t1 - slots_t1[c2][1]) == 1 and
                        aula_t1 == slots_t2[c2][1] and
                        aula_t2 == slots_t1[c2][1]):
                        sucesso = True

                if sucesso:
                    dia = slots_t1[c1][0]
                    aulas = sorted([slots_t1[c1][1], slots_t1[c2][1]])
                    print(f"    [OK] {t1} <---> {t2}: ESPELHADOS com sucesso na {dia} (Aulas {aulas[0]} e {aulas[1]})")
                else:
                    print(f"    [X]  {t1} <---> {t2}: FALHOU em espelhar.")
                    # Mostra onde as aulas foram parar para ajudar o usuário a entender o porquê
                    loc_t1 = f"{slots_t1.get(c1, 'Não alocado')}/{slots_t1.get(c2, 'Não alocado')}"
                    loc_t2 = f"{slots_t2.get(c1, 'Não alocado')}/{slots_t2.get(c2, 'Não alocado')}"
                    print(f"         -> {t1} ficou em: {loc_t1}")
                    print(f"         -> {t2} ficou em: {loc_t2}")

            # 3. Informar sobre turmas assimétricas
            if dados_analise["assimetricos"]:
                print("\n  [INFORMAÇÃO] Turmas tratadas apenas com adjacência local (sem 'X' devido à atribuição):")
                for t, p1, p2 in dados_analise["assimetricos"]:
                    slots_t = alocacoes.get(t, {})
                    loc = f"{slots_t.get(c1, 'Não alocado')}/{slots_t.get(c2, 'Não alocado')}"
                    print(f"    * {t}: Alocadas em sequência no horário: {loc}")

        print("="*80 + "\n")