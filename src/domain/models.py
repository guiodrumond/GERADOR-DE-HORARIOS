from dataclasses import dataclass


@dataclass(frozen=True)
class Curso:
    """
    Representa um curso técnico.

    Exemplo:
    ADM, MMD, TI, IA, PUB, GSD.
    """

    nome_curso: str
    codigo: str
    especialidade_ftp: str
    padrao_ftp: str


@dataclass(frozen=True)
class Turma:
    """
    Representa uma turma ativa ou inativa do sistema.
    """

    codigo: str
    curso: str
    padrao_ftp: str
    ativa: bool


@dataclass(frozen=True)
class Professor:
    """
    Representa um professor e sua especialidade principal.
    """

    nome: str
    especialidade: str
    componente: str
    carga_horaria: int
    max_dias: int
    ativo: bool


@dataclass(frozen=True)
class Especialidade:
    """
    Representa uma especialidade/componente curricular do 1º ano.

    Exemplo:
    POR, MAT, FIS, QUI, HIS, SOC, FTP, PROJ.
    """

    id: int
    componente: str
    nome: str
    sigla: str
    aulas: int


@dataclass(frozen=True)
class Peso:
    """
    Representa um peso de otimização vindo da aba PESOS.
    """

    objetivo: str
    nivel: int
    peso: int


@dataclass(frozen=True)
class Restricao:
    """
    Representa uma regra parametrizada da aba RESTRICOES.
    """

    regra: str
    valor: str


@dataclass(frozen=True)
class Atribuicao:
    """
    Representa a atribuição atual de uma especialidade a um professor em uma turma.
    """

    turma: str
    especialidade: str
    professor: str


@dataclass(frozen=True)
class ParPedagogico:
    """
    Representa duas especialidades que precisam formar um bloco inseparável.
    """

    codigo: str
    especialidade_1: str
    especialidade_2: str


@dataclass(frozen=True)
class PadraoPedagogico:
    """
    Representa padrões pedagógicos parametrizados.

    Exemplo:
    CHSA BLOCO_OTIMO 6
    PROJ FIXO TER1-TER4
    FTP BLOCO4 S
    """

    componente: str
    tipo: str
    valor: str


@dataclass(frozen=True)
class Slot:
    """
    Representa um slot possível da semana.

    Exemplo:
    SEG aula 1, TER aula 4.
    """

    dia: str
    aula: int


@dataclass(frozen=True)
class AreaCurso:
    """
    Representa a área de negócio/pedagógica associada ao curso.

    Exemplo:
    TI -> Tecnologia
    ADM -> Negocios
    MMD -> Multimidia
    """

    curso: str
    area: str


@dataclass(frozen=True)
class AfinidadeArea:
    """
    Representa o custo de proximidade entre áreas de cursos.
    """

    area_a: str
    area_b: str
    custo: int

@dataclass(frozen=True)
class BlocoPedagogico:
    """
    Unidade básica que será posicionada pelo solver.

    Um bloco pode representar:
    - uma disciplina
    - um par pedagógico
    - FTP
    - Projetos

    O solver trabalha com blocos e não com disciplinas.
    """

    id: str

    turma: str

    componentes: list[str]

    tamanho: int

    fixo: bool = False