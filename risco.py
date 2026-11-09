NIVEIS = ("NORMAL", "ATENÇÃO", "PERIGO")

LIMITE_CALOR_ATENCAO = 32
LIMITE_CALOR_PERIGO = 39

LIMITE_CHUVA_HORA_ATENCAO = 20
LIMITE_CHUVA_HORA_PERIGO = 30
LIMITE_CHUVA_DIA_ATENCAO = 50
LIMITE_CHUVA_DIA_PERIGO = 100

def calcular_indice_calor(temp_c, umidade):
    """Calcula o índice de calor (sensação térmica) em graus Celsius.

    Segue o critério da NOAA, que trabalha em fahrenheit:
    1. Calcula a fórmula simples de Steadman.
    2. Se a média entre esse valor e a temperatura for menor que 80 °F,
       o índice é o valor da fórmula simples.
    3. Senão, usa a regressão de Rothfusz.
    Os ajustes finos da NOAA (umidade < 13% ou > 85%) ficam de fora.

    O valor é arredondado só na exibição.
    """

    temp_f = (temp_c * 1.8) + 32

    simples = 0.5 * (temp_f + 61 + (temp_f - 68) * 1.2 + umidade * 0.094)

    if (temp_f + simples) / 2 < 80:
        indice_calor_f = simples
    else:
        indice_calor_f = (
            -42.379
            + 2.04901523 * temp_f
            + 10.14333127 * umidade
            - 0.22475541 * temp_f * umidade
            - 0.00683783 * temp_f ** 2
            - 0.05481717 * umidade ** 2
            + 0.00122874 * temp_f ** 2 * umidade
            + 0.00085282 * temp_f * umidade ** 2
            - 0.00000199 * temp_f ** 2 * umidade ** 2
        )
    
    indice_calor_c = (indice_calor_f - 32) / 1.8

    return indice_calor_c


def nivel_calor(indice):
    """Classifica o índice de calor (graus Celsius) em um dos NIVEIS, pelas faixas da NOAA."""

    if indice < LIMITE_CALOR_ATENCAO:
        return NIVEIS[0]
    elif indice < LIMITE_CALOR_PERIGO:
        return NIVEIS[1]
    else:
        return NIVEIS[2]


def nivel_chuva(mm_hora, mm_dia):
    """Classifica a chuva prevista em um dos NIVEIS, pela escala do INMET.

    Basta um dos critérios (por hora ou por dia) para subir o nível.
    """

    if mm_hora >= LIMITE_CHUVA_HORA_PERIGO or mm_dia >= LIMITE_CHUVA_DIA_PERIGO:
        return NIVEIS[2]
    elif mm_hora >= LIMITE_CHUVA_HORA_ATENCAO or mm_dia >= LIMITE_CHUVA_DIA_ATENCAO:
        return NIVEIS[1]
    else:
        return NIVEIS[0]


def calcular_taxa(indice_atual, indice_anterior, horas):
    """Taxa de variação do índice de calor em graus Celsius/h (derivada discreta).

    Se o intervalo for zero ou negativo, não há como medir tendência,
    então devolve 0.0, o que faz a projeção ficar igual ao valor atual.
    """
    
    if horas <= 0:
        return 0.0
    taxa = (indice_atual - indice_anterior) / horas
    return taxa

def projetar_valor(valor_atual, taxa, horas=1):
    """Estima um valor daqui a x horas (aproximação linear)."""

    indice_projetado = valor_atual + taxa * horas
    return indice_projetado