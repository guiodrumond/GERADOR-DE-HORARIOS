import logging
import re
from collections import defaultdict


class PreflightValidator:

    def __init__(
        self,
        base,
    ):

        self.base = base

        self.problemas = []
        self.resumo_professores = []
        self.detalhes_carga = {}

        self.turmas_por_codigo = (
            self._criar_mapa_turmas()
        )

        self.especialidades_por_ano_sigla = (
            self._criar_mapa_especialidades_por_ano()
        )

        self.especialidades_por_sigla = (
            self._criar_mapa_especialidades_por_sigla()
        )

        self.todos_slots = (
            self._criar_conjunto_slots()
        )

        self.max_dias_por_professor = (
            self._criar_mapa_max_dias()
        )

    # ==================================================
    # VALIDAÇÃO
    # ==================================================

    def validate(self):

        self.problemas = []
        self.resumo_professores = []
        self.detalhes_carga = {}

        carga_por_professor = (
            self._calcular_carga_por_professor()
        )

        bloqueios_por_professor = (
            self._carregar_bloqueios_por_professor()
        )

        for professor in sorted(
            carga_por_professor
        ):

            carga = carga_por_professor[
                professor
            ]

            slots_bloqueados = (
                bloqueios_por_professor.get(
                    professor,
                    set(),
                )
                & self.todos_slots
            )

            slots_disponiveis = (
                len(self.todos_slots)
                - len(slots_bloqueados)
            )

            deficit = max(
                0,
                carga - slots_disponiveis,
            )

            max_dias, capacidade_max_dias = (
                self._capacidade_max_dias(
                    professor,
                    slots_bloqueados,
                )
            )

            deficit_max_dias = 0

            if capacidade_max_dias is not None:

                deficit_max_dias = max(
                    0,
                    carga - capacidade_max_dias,
                )

            status = (
                "ERRO"
                if deficit > 0 or deficit_max_dias > 0
                else "OK"
            )

            resumo = {
                "professor": professor,
                "carga": carga,
                "slots_totais": len(
                    self.todos_slots
                ),
                "slots_bloqueados": len(
                    slots_bloqueados
                ),
                "slots_disponiveis": slots_disponiveis,
                "deficit": deficit,
                "max_dias": max_dias,
                "capacidade_max_dias": capacidade_max_dias,
                "deficit_max_dias": deficit_max_dias,
                "status": status,
            }

            self.resumo_professores.append(
                resumo
            )

            if deficit > 0:

                self.problemas.append(
                    {
                        "tipo": "CH_MAIOR_QUE_DISPONIBILIDADE",
                        **resumo,
                    }
                )

            if deficit_max_dias > 0:

                self.problemas.append(
                    {
                        "tipo": "CH_MAIOR_QUE_CAPACIDADE_MAX_DIAS",
                        **resumo,
                    }
                )

        return self.problemas

    def is_valid(self):

        return not self.problemas

    # ==================================================
    # RELATÓRIO
    # ==================================================

    def log_report(self):

        if not self.resumo_professores:

            self.validate()

        logging.info(
            "============================================================"
        )

        logging.info(
            "🔎 PRÉ-VALIDAÇÃO: CH X DISPONIBILIDADE X MAX DIAS"
        )

        logging.info(
            "============================================================"
        )

        logging.info(
            "Slots semanais considerados: %s",
            len(self.todos_slots),
        )

        logging.info(
            "Professores analisados: %s",
            len(self.resumo_professores),
        )

        logging.info(
            "Problemas encontrados: %s",
            len(self.problemas),
        )

        for item in self.resumo_professores:

            if item["status"] == "OK":

                logging.info(
                    "✅ %s | CH: %s | Bloqueados: %s "
                    "| Disponíveis: %s | Max Dias: %s "
                    "| Capacidade: %s",
                    item["professor"],
                    item["carga"],
                    item["slots_bloqueados"],
                    item["slots_disponiveis"],
                    item["max_dias"],
                    item["capacidade_max_dias"],
                )

                continue

            logging.error(
                "❌ %s | CH: %s | Disponíveis: %s "
                "| Déficit disp.: %s | Max Dias: %s "
                "| Capacidade: %s | Déficit dias: %s",
                item["professor"],
                item["carga"],
                item["slots_disponiveis"],
                item["deficit"],
                item["max_dias"],
                item["capacidade_max_dias"],
                item["deficit_max_dias"],
            )

            detalhes = self.detalhes_carga.get(
                item["professor"],
                [],
            )

            logging.error(
                "   COMPOSIÇÃO DA CH:"
            )

            soma = 0

            for detalhe in detalhes:

                soma += detalhe["aulas"]

                logging.error(
                    "   ↳ Turma: %s | Ano: %s "
                    "| Especialidade: %s | CH: %s "
                    "| Origem: %s",
                    detalhe["turma"],
                    detalhe["ano"],
                    detalhe["especialidade"],
                    detalhe["aulas"],
                    detalhe["origem"],
                )

            logging.error(
                "   └─ TOTAL CONFERIDO: %s",
                soma,
            )

        logging.info(
            "============================================================"
        )

    # ==================================================
    # CARGA HORÁRIA
    # ==================================================

    def _calcular_carga_por_professor(
        self,
    ):

        carga = defaultdict(int)
        detalhes = defaultdict(list)
        processadas = set()

        for atribuicao in self.base.atribuicoes:

            professor = self._normalizar(
                atribuicao.professor
            )

            turma = self._normalizar(
                atribuicao.turma
            )

            especialidade = self._normalizar(
                atribuicao.especialidade
            )

            if not professor:
                continue

            chave = (
                professor,
                turma,
                especialidade,
            )

            if chave in processadas:

                logging.warning(
                    "Atribuição duplicada ignorada: %s | %s | %s",
                    professor,
                    turma,
                    especialidade,
                )

                continue

            processadas.add(
                chave
            )

            ano = self._ano_da_turma(
                turma
            )

            especialidade_obj, origem = (
                self._buscar_especialidade(
                    ano,
                    especialidade,
                )
            )

            if especialidade_obj is None:

                logging.warning(
                    "Especialidade não encontrada: %s "
                    "| Turma: %s | Ano: %s | Professor: %s",
                    especialidade,
                    turma,
                    ano,
                    professor,
                )

                continue

            aulas = int(
                especialidade_obj.aulas
            )

            carga[professor] += aulas

            detalhes[professor].append(
                {
                    "turma": turma,
                    "ano": ano,
                    "especialidade": especialidade,
                    "aulas": aulas,
                    "origem": origem,
                }
            )

        self.detalhes_carga = dict(
            detalhes
        )

        return dict(
            carga
        )

    def _buscar_especialidade(
        self,
        ano,
        sigla,
    ):

        if ano is not None:

            especialidade = (
                self.especialidades_por_ano_sigla.get(
                    (
                        ano,
                        sigla,
                    )
                )
            )

            if especialidade is not None:

                return (
                    especialidade,
                    "ANO+SIGLA",
                )

        candidatas = self.especialidades_por_sigla.get(
            sigla,
            [],
        )

        if len(candidatas) == 1:

            return (
                candidatas[0],
                "SIGLA",
            )

        if len(candidatas) > 1:

            logging.warning(
                "Especialidade ambígua sem ano identificado: "
                "%s | Ano da turma: %s",
                sigla,
                ano,
            )

        return (
            None,
            "NAO_ENCONTRADA",
        )

    def _ano_da_turma(
        self,
        codigo_turma,
    ):

        turma = self.turmas_por_codigo.get(
            codigo_turma
        )

        if turma is not None:

            ano_normalizado = self._normalizar_ano(
                getattr(
                    turma,
                    "ano",
                    None,
                )
            )

            if ano_normalizado is not None:
                return ano_normalizado

        match = re.match(
            r"^(\d+)",
            codigo_turma,
        )

        if match:

            return int(
                match.group(1)
            )

        return None

    # ==================================================
    # MAX DIAS
    # ==================================================

    def _criar_mapa_max_dias(
        self,
    ):

        mapa = {}

        for professor in getattr(
            self.base,
            "professores",
            [],
        ) or []:

            nome = self._normalizar(
                getattr(
                    professor,
                    "nome",
                    "",
                )
            )

            max_dias = self._normalizar_ano(
                getattr(
                    professor,
                    "max_dias",
                    None,
                )
            )

            if not nome or not max_dias:
                continue

            if nome in mapa and mapa[nome] != max_dias:

                logging.warning(
                    "Professor duplicado com Max Dias diferentes: "
                    "%s | %s e %s. Usando o mais restritivo.",
                    nome,
                    mapa[nome],
                    max_dias,
                )

                mapa[nome] = min(
                    mapa[nome],
                    max_dias,
                )

                continue

            mapa[nome] = max_dias

        return mapa

    def _capacidade_max_dias(
        self,
        professor,
        slots_bloqueados,
    ):

        max_dias = self.max_dias_por_professor.get(
            professor
        )

        if not max_dias:

            return (
                None,
                None,
            )

        livres_por_dia = defaultdict(int)

        for slot in self.todos_slots:

            if slot in slots_bloqueados:
                continue

            dia = slot.split("_")[0]

            livres_por_dia[dia] += 1

        melhores_dias = sorted(
            livres_por_dia.values(),
            reverse=True,
        )[:max_dias]

        return (
            max_dias,
            sum(melhores_dias),
        )

    # ==================================================
    # DISPONIBILIDADE
    # ==================================================

    def _carregar_bloqueios_por_professor(
        self,
    ):

        resultado = {}

        disponibilidade = getattr(
            self.base,
            "disponibilidade",
            {},
        ) or {}

        for professor, slots in disponibilidade.items():

            resultado[
                self._normalizar(
                    professor
                )
            ] = {
                self._normalizar_slot(
                    slot
                )
                for slot in slots
                if slot
            }

        return resultado

    # ==================================================
    # MAPAS
    # ==================================================

    def _criar_mapa_turmas(
        self,
    ):

        mapa = {}

        for turma in self.base.turmas:

            codigo = self._normalizar(
                getattr(
                    turma,
                    "codigo",
                    "",
                )
            )

            if codigo:
                mapa[codigo] = turma

        return mapa

    def _criar_mapa_especialidades_por_ano(
        self,
    ):

        mapa = {}

        for especialidade in self.base.especialidades:

            ano = self._normalizar_ano(
                getattr(
                    especialidade,
                    "ano",
                    None,
                )
            )

            if ano is None:
                continue

            sigla = self._normalizar(
                especialidade.sigla
            )

            chave = (
                ano,
                sigla,
            )

            if chave in mapa:

                logging.warning(
                    "Especialidade duplicada para o mesmo ano: "
                    "Ano %s | %s",
                    ano,
                    sigla,
                )

            mapa[chave] = especialidade

        return mapa

    def _criar_mapa_especialidades_por_sigla(
        self,
    ):

        mapa = defaultdict(list)

        for especialidade in self.base.especialidades:

            sigla = self._normalizar(
                especialidade.sigla
            )

            mapa[sigla].append(
                especialidade
            )

        return dict(
            mapa
        )

    def _criar_conjunto_slots(
        self,
    ):

        return {
            self._normalizar_slot(
                slot
            )
            for slot in self.base.slots
        }

    # ==================================================
    # UTIL
    # ==================================================

    def _normalizar(
        self,
        valor,
    ):

        if valor is None:
            return ""

        return str(
            valor
        ).strip().upper()

    def _normalizar_ano(
        self,
        valor,
    ):

        if valor is None:
            return None

        match = re.search(
            r"\d+",
            str(valor).strip(),
        )

        if not match:
            return None

        return int(
            match.group()
        )

    def _normalizar_slot(
        self,
        slot,
    ):

        if hasattr(
            slot,
            "dia",
        ) and hasattr(
            slot,
            "aula",
        ):

            return (
                f"{str(slot.dia).strip().upper()}_"
                f"{int(float(slot.aula))}"
            )

        if isinstance(
            slot,
            tuple,
        ) and len(slot) == 2:

            return (
                f"{str(slot[0]).strip().upper()}_"
                f"{int(float(slot[1]))}"
            )

        texto = str(
            slot
        ).strip().upper()

        partes = (
            texto
            .replace(
                "_",
                " ",
            )
            .split()
        )

        if len(partes) == 2:

            try:

                return (
                    f"{partes[0]}_"
                    f"{int(float(partes[1]))}"
                )

            except ValueError:

                return (
                    f"{partes[0]}_"
                    f"{partes[1]}"
                )

        return texto