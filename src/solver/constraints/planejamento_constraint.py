import logging
from collections import defaultdict

from src.domain.matchers import PlanejamentoMatcher


class PlanejamentoConstraint:

    INVALIDOS = {"NONE", "NAN", "", "A DEFINIR"}

    def __init__(self, model, variables, base, atribuicoes_map):
        self.model = model
        self.variables = variables  # {bloco.id: {slot_inicio_id: bool_var}}
        self.base = base
        self.atribuicoes_map = atribuicoes_map
        self.matcher = PlanejamentoMatcher(base)

        self.reuniao_vars = {}  # Usado pelo GridBuilder e MaxDias
        self.mapa_professores = {}
        self.participantes_por_plano = {}
        self.grupo_por_plano = {}

    # ==================================================
    # APOIO
    # ==================================================

    def _norm(self, valor):
        return "" if valor is None else str(valor).strip().upper()

    def _criar_mapa_professores(self):
        mapa = defaultdict(set)

        for atribuicao in self.base.atribuicoes:
            prof = self._norm(atribuicao.professor)

            if prof in self.INVALIDOS:
                continue

            chave = (self._norm(atribuicao.turma), self._norm(atribuicao.especialidade))
            mapa[chave].add(prof)

        return mapa

    def _professores_do_bloco(self, bloco):
        professores = set()

        for componente in bloco.componentes:
            chave = (self._norm(bloco.turma), self._norm(componente))
            professores |= self.mapa_professores.get(chave, set())

        return professores

    def _parse_slot_id(self, slot_id):
        partes = slot_id.split("_")
        return partes[0], int(float(partes[1]))

    def _bloco_ocupa_slot(self, bloco, slot_inicio_id, slot_alvo_id):
        dia_inicio, aula_inicio = self._parse_slot_id(slot_inicio_id)
        dia_alvo, aula_alvo = self._parse_slot_id(slot_alvo_id)

        if dia_inicio != dia_alvo:
            return False

        aula_final = aula_inicio + bloco.tamanho - 1
        return aula_inicio <= aula_alvo <= aula_final

    def _slot_ids(self):
        return [f"{slot.dia}_{slot.aula}" for slot in self.base.slots]

    # ==================================================
    # BUILD
    # ==================================================

    def build(self):
        self.mapa_professores = self._criar_mapa_professores()

        # Pré-calcula os professores de cada bloco (uma única vez)
        professores_por_bloco = {
            bloco.id: self._professores_do_bloco(bloco)
            for bloco in self.base.blocos
        }

        # Agrupa as aulas por dia
        dias_slots = defaultdict(set)

        for slot in self.base.slots:
            dias_slots[slot.dia].add(slot.aula)

        slot_ids = self._slot_ids()

        for plan in self.base.planejamentos:

            participantes = {
                self._norm(p)
                for p in self.matcher.filtrar_professores(plan)
                if self._norm(p) not in self.INVALIDOS
            }

            if not participantes:
                continue

            self.participantes_por_plano[plan.nome] = participantes
            self.grupo_por_plano[plan.nome] = self._norm(getattr(plan, "grupo", None))
            self.reuniao_vars[plan.nome] = {}

            tamanho = int(plan.tamanho)
            window_vars = []
            slot_to_windows = {s: [] for s in slot_ids}

            # Janelas contínuas no mesmo dia
            for dia, aulas in dias_slots.items():
                aulas_ord = sorted(aulas)

                for i in range(len(aulas_ord) - tamanho + 1):
                    janela = aulas_ord[i:i + tamanho]

                    if janela != list(range(janela[0], janela[0] + tamanho)):
                        continue

                    w_var = self.model.NewBoolVar(
                        f"plan_{plan.nome}_{dia}_aulas_{janela[0]}_to_{janela[-1]}"
                    )
                    window_vars.append(w_var)

                    for a in janela:
                        s_id = f"{dia}_{a}"
                        if s_id in slot_to_windows:
                            slot_to_windows[s_id].append(w_var)

            if not window_vars:
                continue

            # 1. Exatamente UMA janela para a reunião
            self.model.Add(sum(window_vars) == 1)

            # 2. Variável de ativação por slot
            for slot_id in slot_ids:
                slot_active = self.model.NewBoolVar(f"plan_active_{plan.nome}_{slot_id}")
                self.reuniao_vars[plan.nome][slot_id] = slot_active

                cobertura = slot_to_windows.get(slot_id, [])

                if cobertura:
                    self.model.Add(slot_active == sum(cobertura))
                else:
                    self.model.Add(slot_active == 0)

            # 3. Convocados não podem ter aula durante a reunião
            blocos_envolvidos = [
                bloco for bloco in self.base.blocos
                if not professores_por_bloco[bloco.id].isdisjoint(participantes)
            ]

            for slot_id in slot_ids:
                aulas = []

                for bloco in blocos_envolvidos:
                    for slot_inicio_id, var_bloco in self.variables.get(bloco.id, {}).items():
                        if self._bloco_ocupa_slot(bloco, slot_inicio_id, slot_id):
                            aulas.append(var_bloco)

                if aulas:
                    self.model.Add(sum(aulas) == 0).OnlyEnforceIf(
                        self.reuniao_vars[plan.nome][slot_id]
                    )

        # 4. Não sobreposição
        self._aplicar_nao_sobreposicao(slot_ids)

    # ==================================================
    # REGRA 4
    # ==================================================

    def _aplicar_nao_sobreposicao(self, slot_ids):

        # 4a. Reuniões do mesmo GRUPO não coincidem
        reunioes_por_grupo = defaultdict(list)

        for nome, grupo in self.grupo_por_plano.items():
            if grupo:
                reunioes_por_grupo[grupo].append(nome)

        for grupo, nomes in reunioes_por_grupo.items():
            if len(nomes) < 2:
                continue

            for slot_id in slot_ids:
                self.model.Add(
                    sum(self.reuniao_vars[n][slot_id] for n in nomes) <= 1
                )

        # 4b. Um professor não pode estar em duas reuniões ao mesmo tempo
        reunioes_por_professor = defaultdict(list)

        for nome, participantes in self.participantes_por_plano.items():
            for prof in participantes:
                reunioes_por_professor[prof].append(nome)

        restricoes_professor = 0

        for prof, nomes in reunioes_por_professor.items():
            if len(nomes) < 2:
                continue

            for slot_id in slot_ids:
                self.model.Add(
                    sum(self.reuniao_vars[n][slot_id] for n in nomes) <= 1
                )

            restricoes_professor += 1

        logging.info("🔗 Regra de sobreposição de planejamentos:")

        for grupo, nomes in sorted(reunioes_por_grupo.items()):
            logging.info(
                f"   Grupo {grupo}: {len(nomes)} reuniões "
                f"({len(nomes) * 2} slots exigidos) | {', '.join(nomes)}"
            )

        sem_grupo = [n for n, g in self.grupo_por_plano.items() if not g]

        if sem_grupo:
            logging.warning(f"   ⚠️ Sem grupo: {', '.join(sem_grupo)}")

        logging.info(
            f"   Professores em mais de uma reunião (travados entre si): {restricoes_professor}"
        )