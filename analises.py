import math
import os
import matplotlib.pyplot as plt
from risco import calcular_indice_calor, LIMITE_CALOR_ATENCAO, LIMITE_CALOR_PERIGO

PASTA_GRAFICOS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "graficos")

HORA_PICO = 17
UMIDADE = 50

# (nome, temperatura média, amplitude)
CENARIOS = (
    ("Dia comum", 27, 3),
    ("Dia extremo", 30, 3.5),
    ("Casa com pouco isolamento", 30, 4.5),
)


def temperatura(t, media, amplitude):
    """Temperatura dentro de casa (°C) na hora t, com pico às 17h."""
    return media + amplitude * math.cos(2 * math.pi / 24 * (t - HORA_PICO))


def gerar_horas(passo=0.1):
    """Lista de horas de 0 a 24, com o passo dado (0.1 h = 6 min)."""
    quantidade = round(24 / passo)
    return [i * passo for i in range(quantidade + 1)]


def grafico_indice_ao_longo_do_dia():
    horas = gerar_horas()

    plt.figure(figsize=(9, 5))

    for nome, media, amplitude in CENARIOS:
        indices = [calcular_indice_calor(temperatura(t, media, amplitude), UMIDADE) for t in horas]
        plt.plot(horas, indices, label=nome)

    plt.axhline(LIMITE_CALOR_ATENCAO, color="orange", linestyle="--", label="ATENÇÃO (32 °C)")
    plt.axhline(LIMITE_CALOR_PERIGO, color="red", linestyle="--", label="PERIGO (39 °C)")

    plt.title(f"Índice de calor dentro de casa ao longo do dia (UR = {UMIDADE}%)")
    plt.xlabel("Hora do dia")
    plt.ylabel("Índice de calor (°C)")
    plt.xticks(range(0, 25, 2))
    plt.xlim(0, 24)
    plt.ylim(22, 43)
    plt.grid(alpha=0.3)
    plt.legend(loc="upper left", ncol=2)
    plt.tight_layout()

    os.makedirs(PASTA_GRAFICOS, exist_ok=True)
    plt.savefig(os.path.join(PASTA_GRAFICOS, "01_indice_ao_longo_do_dia.png"), dpi=150)
    plt.show()


def fronteira_noaa(umidade):
    """Temperatura T* (°C) em que o índice troca da fórmula simples para Rothfusz.
 
    Com a umidade fixa, a fórmula simples é uma reta em T (°F):
    simples(T) = 1,1·T - 10,3 + 0,047·UR. Resolvendo (T + simples(T)) / 2 = 80:
    T* = (170,3 - 0,047·UR) / 2,1   (em °F)
    """
    t_estrela_f = (170.3 - 0.047 * umidade) / 2.1
    return (t_estrela_f - 32) / 1.8
 
 
def instante_subida(temp_alvo, media, amplitude):
    """Hora (antes do pico) em que T(t) passa por temp_alvo, pelo arco-cosseno."""
    angulo = math.acos((temp_alvo - media) / amplitude)
    return HORA_PICO - angulo * 24 / (2 * math.pi)
 
 
def grafico_zoom_descontinuidade():
    """Zoom no degrau do dia comum: a linha é cortada no instante do salto."""
    nome, media, amplitude = CENARIOS[0]
    t_estrela = instante_subida(fronteira_noaa(UMIDADE), media, amplitude)
 
    def ic_no_tempo(t):
        return calcular_indice_calor(temperatura(t, media, amplitude), UMIDADE)
 
    passo = 0.001
    antes = [t_estrela - 0.4 + i * passo for i in range(round(0.4 / passo))]
    depois = [t_estrela + i * passo for i in range(1, round(0.4 / passo) + 1)]
 
    # Limites laterais: à esquerda vale a fórmula simples, à direita, Rothfusz.
    # Em t* exato o teste "< 80" dá falso, então o valor da função é o da direita.
    limite_esquerda = ic_no_tempo(t_estrela - 1e-9)
    valor_em_t = ic_no_tempo(t_estrela)
 
    plt.figure(figsize=(8, 5))
    plt.plot(antes, [ic_no_tempo(t) for t in antes], color="tab:blue", label="Fórmula simples (Steadman)")
    plt.plot(depois, [ic_no_tempo(t) for t in depois], color="tab:purple", label="Regressão de Rothfusz")
 
    plt.plot(t_estrela, limite_esquerda, "o", markerfacecolor="white", color="tab:blue", markersize=8)
    plt.plot(t_estrela, valor_em_t, "o", color="tab:purple", markersize=8)
 
    plt.axvline(t_estrela, color="gray", linestyle=":", linewidth=1)
    plt.annotate(f"salto ≈ {valor_em_t - limite_esquerda:.2f} °C",
                 xy=(t_estrela, (valor_em_t + limite_esquerda) / 2),
                 xytext=(t_estrela + 0.08, (valor_em_t + limite_esquerda) / 2 - 0.15),
                 arrowprops={"arrowstyle": "->", "color": "gray"})
 
    horas = int(t_estrela)
    minutos = round((t_estrela - horas) * 60)
    plt.title(f"{nome}: descontinuidade do índice de calor às {horas}h{minutos:02d} (T* ≈ {fronteira_noaa(UMIDADE):.2f} °C)")
    plt.xlabel("Hora do dia")
    plt.ylabel("Índice de calor (°C)")
    plt.grid(alpha=0.3)
    plt.legend(loc="upper left")
    plt.tight_layout()
 
    os.makedirs(PASTA_GRAFICOS, exist_ok=True)
    plt.savefig(os.path.join(PASTA_GRAFICOS, "02_zoom_descontinuidade.png"), dpi=150)
    plt.show()

def derivada_temperatura(t, media, amplitude):
    """Derivada exata de T(t), em °C/h: T'(t) = -A·(2π/24)·sen(2π/24·(t - 17))."""
    return -amplitude * (2 * math.pi / 24) * math.sin(2 * math.pi / 24 * (t - HORA_PICO))
 
 
def tabela_taxa_como_limite(t=11, cenario=1, passos=(1, 0.5, 1 / 6, 0.1, 0.01, 0.001)):
    """Mostra a taxa média (T(t) - T(t - h)) / h se aproximando de T'(t) quando h → 0.
 
    É a mesma razão que o risco.py calcula com duas leituras do sensor.
    h = 1/6 h corresponde a leituras a cada 10 minutos.
    """
    nome, media, amplitude = CENARIOS[cenario]
    exata = derivada_temperatura(t, media, amplitude)
 
    print(f"\n{nome}, t = {t}h  |  derivada exata T'({t}) = {exata:.4f} °C/h")
    print(f"{'h (h)':>8} {'h (min)':>8} {'taxa média':>12} {'erro':>10} {'erro %':>8}")
 
    for h in passos:
        media_h = (temperatura(t, media, amplitude) - temperatura(t - h, media, amplitude)) / h
        erro = media_h - exata
        print(f"{h:>8.3f} {h * 60:>8.1f} {media_h:>12.4f} {erro:>10.4f} {abs(erro) / abs(exata) * 100:>7.2f}%")

def derivada_indice_calor(temp_c, umidade):
    """dIC/dT (adimensional: °C/°C = °F/°F), com a umidade fixa.
 
    Abaixo da fronteira T*, o índice é a fórmula simples 1,1·T + constante,
    então a derivada é 1,1. Acima, é a derivada da regressão de Rothfusz,
    obtida termo a termo tratando a umidade como constante.
    """
    if temp_c < fronteira_noaa(umidade):
        return 1.1
 
    t = temp_c * 1.8 + 32
    u = umidade
    return (
        2.04901523
        - 0.22475541 * u
        - 2 * 0.00683783 * t
        + 2 * 0.00122874 * t * u
        + 0.00085282 * u ** 2
        - 2 * 0.00000199 * t * u ** 2
    )
 
 
def grafico_derivada_indice():
    """dIC/dT em função da temperatura, para três umidades."""
    umidades = ((50, "tab:blue"), (60, "tab:orange"), (70, "tab:red"))
    t_min, t_max, passo = 24, 36, 0.01
 
    plt.figure(figsize=(9, 5))
 
    temps = [t_min + i * passo for i in range(round((t_max - t_min) / passo) + 1)]
 
    # Abaixo de T*, a derivada é 1,1 para qualquer umidade (fórmula simples).
    # Desenha um único trecho cinza até o maior T*, para as três linhas não se sobreporem.
    maior_t_estrela = max(fronteira_noaa(u) for u, _ in umidades)
    trecho_simples = [t for t in temps if t < maior_t_estrela]
    plt.plot(trecho_simples, [1.1] * len(trecho_simples), color="dimgray",
             label="Fórmula simples: dIC/dT = 1,1 (qualquer UR)")
 
    for umidade, cor in umidades:
        t_estrela = fronteira_noaa(umidade)
        depois = [t for t in temps if t >= t_estrela]
 
        plt.plot(depois, [derivada_indice_calor(t, umidade) for t in depois], color=cor,
                 label=f"Rothfusz, UR = {umidade}% (T* = {t_estrela:.2f} °C)")
 
        # Em T*: círculo vazio = fim da fórmula simples; círculo cheio = início de Rothfusz.
        plt.plot(t_estrela, 1.1, "o", markerfacecolor="white", color=cor, markersize=6)
        plt.plot(t_estrela, derivada_indice_calor(t_estrela, umidade), "o", color=cor, markersize=6)
        plt.plot([t_estrela, t_estrela], [1.1, derivada_indice_calor(t_estrela, umidade)],
                 color=cor, linestyle=":", linewidth=1)
 
    plt.axhline(1, color="gray", linestyle=":", linewidth=1)
    plt.text(t_max - 0.1, 1.04, "dIC/dT = 1 (sensação acompanha a temperatura)",
             ha="right", fontsize="small", color="gray")
 
    plt.title("Quanto a sensação térmica sobe a cada +1 °C dentro de casa")
    plt.xlabel("Temperatura dentro de casa (°C)")
    plt.ylabel("dIC/dT (°C de sensação por °C)")
    plt.xlim(t_min, t_max)
    plt.grid(alpha=0.3)
    plt.legend(loc="upper left")
    plt.tight_layout()
 
    os.makedirs(PASTA_GRAFICOS, exist_ok=True)
    plt.savefig(os.path.join(PASTA_GRAFICOS, "03_derivada_indice.png"), dpi=150)
    plt.show()

def velocidade_sensacao(t, media, amplitude, umidade=UMIDADE):
    """dIC/dt pela regra da cadeia: dIC/dT · T'(t), em °C de sensação por hora."""
    temp = temperatura(t, media, amplitude)
    return derivada_indice_calor(temp, umidade) * derivada_temperatura(t, media, amplitude)
 
 
def grafico_regra_da_cadeia(cenario=1, inicio=8, fim=20):
    """Velocidade da temperatura (T') e da sensação térmica (dIC/dt) ao longo do dia.
 
    O intervalo de 8h a 20h fica longe da fronteira T* (no dia extremo ela é
    cruzada às 3h51 e 6h08), onde dIC/dT salta.
    """
    nome, media, amplitude = CENARIOS[cenario]
    passo = 0.01
    horas = [inicio + i * passo for i in range(round((fim - inicio) / passo) + 1)]
 
    vel_temp = [derivada_temperatura(t, media, amplitude) for t in horas]
    vel_sens = [velocidade_sensacao(t, media, amplitude) for t in horas]
 
    i_temp = vel_temp.index(max(vel_temp))
    i_sens = vel_sens.index(max(vel_sens))
 
    def hora_texto(t):
        h = int(t)
        return f"{h}h{round((t - h) * 60):02d}"
 
    plt.figure(figsize=(9, 5))
    plt.plot(horas, vel_temp, color="tab:blue", label="Temperatura: T'(t)")
    plt.plot(horas, vel_sens, color="tab:red", label="Sensação térmica: dIC/dt = dIC/dT · T'(t)")
 
    for i, cor, lista in ((i_temp, "tab:blue", vel_temp), (i_sens, "tab:red", vel_sens)):
        plt.plot(horas[i], lista[i], "o", color=cor)
        plt.axvline(horas[i], color=cor, linestyle=":", linewidth=1)
        plt.annotate(f"máx. {lista[i]:.2f} °C/h às {hora_texto(horas[i])}",
                     xy=(horas[i], lista[i]), xytext=(horas[i] + 0.3, lista[i] + 0.08),
                     color=cor, fontsize="small")
 
    plt.axhline(0, color="gray", linewidth=0.8)
    plt.title(f"{nome} (UR = {UMIDADE}%): quão rápido sobem a temperatura e a sensação térmica")
    plt.xlabel("Hora do dia")
    plt.ylabel("Velocidade (°C por hora)")
    plt.xticks(range(inicio, fim + 1))
    plt.xlim(inicio, fim)
    plt.ylim(min(min(vel_temp), min(vel_sens)) - 0.1, max(vel_sens) + 0.35)
    plt.grid(alpha=0.3)
    plt.legend(loc="upper right")
    plt.tight_layout()
 
    os.makedirs(PASTA_GRAFICOS, exist_ok=True)
    plt.savefig(os.path.join(PASTA_GRAFICOS, "04_regra_da_cadeia.png"), dpi=150)
    plt.show()

def projecao_tangente(t0, horizonte, media, amplitude):
    """Projeção linear pela reta tangente em t0: T(t0) + T'(t0) · horizonte."""
    return temperatura(t0, media, amplitude) + derivada_temperatura(t0, media, amplitude) * horizonte
 
 
def projecao_app(t0, horizonte, media, amplitude, intervalo=1 / 6):
    """Projeção como o risco.py faz: taxa com a leitura de 'intervalo' horas atrás."""
    atual = temperatura(t0, media, amplitude)
    taxa = (atual - temperatura(t0 - intervalo, media, amplitude)) / intervalo
    return atual + taxa * horizonte
 
 
def tabela_erro_projecao(cenario=1, horarios=(9, 13, 16), horizontes=(0.25, 0.5, 1, 2)):
    """Erro da projeção linear (projetado − real), em °C, por horário e horizonte."""
    nome, media, amplitude = CENARIOS[cenario]
 
    print(f"\n{nome}: erro da projeção pela reta tangente (projetado − real, °C de temperatura)")
    print(f"{'horário':>8}" + "".join(f"{f'{h * 60:.0f} min':>10}" for h in horizontes) + f"{'app, 1 h':>11}")
 
    for t0 in horarios:
        linha = f"{t0:>7}h"
        for h in horizontes:
            erro = projecao_tangente(t0, h, media, amplitude) - temperatura(t0 + h, media, amplitude)
            linha += f"{erro:>+10.3f}"
        erro_app = projecao_app(t0, 1, media, amplitude) - temperatura(t0 + 1, media, amplitude)
        print(linha + f"{erro_app:>+11.3f}")
 
 
def grafico_retas_tangentes(cenario=1, horarios=(9, 13, 16), inicio=6, fim=20, horizonte=1):
    """Curva T(t) e retas tangentes saindo de alguns horários, com a projeção de 1 h."""
    nome, media, amplitude = CENARIOS[cenario]
    passo = 0.01
    horas = [inicio + i * passo for i in range(round((fim - inicio) / passo) + 1)]
 
    plt.figure(figsize=(9, 5))
    plt.plot(horas, [temperatura(t, media, amplitude) for t in horas], color="black",
             label="Temperatura real (modelo)")
 
    cores = ("tab:green", "tab:orange", "tab:red")
    # Deslocamento vertical de cada rótulo, para não cair em cima das linhas.
    deslocamentos = (-0.45, -0.55, 0.25)
    for t0, cor, desloc in zip(horarios, cores, deslocamentos):
        # A reta é desenhada até 2 h à frente, para mostrar o afastamento crescer.
        trecho = [t0 + i * passo for i in range(round(2 / passo) + 1)]
        plt.plot(trecho, [projecao_tangente(t0, t - t0, media, amplitude) for t in trecho],
                 color=cor, linestyle="--", label=f"Reta tangente às {t0}h")
 
        plt.plot(t0, temperatura(t0, media, amplitude), "o", color=cor)
        projetado = projecao_tangente(t0, horizonte, media, amplitude)
        real = temperatura(t0 + horizonte, media, amplitude)
        plt.plot(t0 + horizonte, projetado, "s", color=cor, markersize=6)
        plt.plot([t0 + horizonte, t0 + horizonte], [real, projetado], color=cor, linewidth=2)
        plt.annotate(f"erro em 1 h: {projetado - real:+.2f} °C", xy=(t0 + horizonte, projetado),
                     xytext=(t0 + horizonte + 0.15, projetado + desloc),
                     color=cor, fontsize="small")
 
    plt.title(f"{nome}: projeção de 1 hora pela reta tangente")
    plt.xlabel("Hora do dia")
    plt.ylabel("Temperatura dentro de casa (°C)")
    plt.xticks(range(inicio, fim + 1))
    plt.xlim(inicio, fim)
    plt.grid(alpha=0.3)
    plt.legend(loc="lower right")
    plt.tight_layout()
 
    os.makedirs(PASTA_GRAFICOS, exist_ok=True)
    plt.savefig(os.path.join(PASTA_GRAFICOS, "05_retas_tangentes.png"), dpi=150)
    plt.show()

def graus_hora(media, amplitude, passo=0.01, limite=LIMITE_CALOR_ATENCAO, umidade=UMIDADE):
    """Exposição ao calor acima do limite, em °C·h: soma de Riemann de (IC − limite) · Δt.
 
    Usa o ponto da esquerda de cada intervalo, como se fossem leituras do sensor
    a cada 'passo' horas. Só os trechos com IC acima do limite entram na soma.
    """
    total = 0
    for i in range(round(24 / passo)):
        excesso = calcular_indice_calor(temperatura(i * passo, media, amplitude), umidade) - limite
        if excesso > 0:
            total += excesso * passo
    return total
 
 
def tabela_graus_hora(passos=(2, 1, 0.5, 1 / 6, 0.01)):
    """Graus-hora acima de 32 °C em cada cenário, para vários tamanhos de intervalo."""
    print("\nGraus-hora acima de 32 °C (°C·h), somas de Riemann")
    print(f"{'cenário':<28}" + "".join(f"{f'{p * 60:.0f} min':>10}" for p in passos))
    for nome, media, amplitude in CENARIOS:
        print(f"{nome:<28}" + "".join(f"{graus_hora(media, amplitude, p):>10.2f}" for p in passos))
 
 
def grafico_graus_hora():
    """À esquerda, a área acima de 32 °C nos cenários; à direita, a soma de Riemann com Δt = 1 h."""
    passo = 0.01
    horas = [i * passo for i in range(round(24 / passo) + 1)]
    limite = LIMITE_CALOR_ATENCAO
 
    fig, (esq, dir_) = plt.subplots(1, 2, figsize=(12, 5), sharey=True)
 
    cores = ("tab:blue", "tab:orange", "tab:green")
    for (nome, media, amplitude), cor in zip(CENARIOS, cores):
        ic = [calcular_indice_calor(temperatura(t, media, amplitude), UMIDADE) for t in horas]
        area = graus_hora(media, amplitude)
        esq.plot(horas, ic, color=cor, label=f"{nome}: {area:.1f} °C·h")
        esq.fill_between(horas, ic, limite, where=[v > limite for v in ic], color=cor, alpha=0.25)
 
    esq.axhline(limite, color="orange", linestyle="--", linewidth=1)
    esq.set_title("Área acima de 32 °C = graus-hora de exposição")
    esq.set_xlabel("Hora do dia")
    esq.set_ylabel("Índice de calor (°C)")
    esq.set_xticks(range(0, 25, 4))
    esq.set_xlim(0, 24)
    esq.grid(alpha=0.3)
    esq.legend(loc="upper left", fontsize="small")
 
    # Soma de Riemann do dia extremo com retângulos de 1 hora (ponto da esquerda).
    nome, media, amplitude = CENARIOS[1]
    ic = [calcular_indice_calor(temperatura(t, media, amplitude), UMIDADE) for t in horas]
    dir_.plot(horas, ic, color="tab:orange", label=nome)
    for h in range(24):
        valor = calcular_indice_calor(temperatura(h, media, amplitude), UMIDADE)
        if valor > limite:
            dir_.bar(h, valor - limite, width=1, bottom=limite, align="edge",
                     color="tab:orange", alpha=0.3, edgecolor="tab:orange")
    dir_.axhline(limite, color="orange", linestyle="--", linewidth=1)
    dir_.set_title(f"Soma de Riemann com Δt = 1 h: {graus_hora(media, amplitude, 1):.1f} °C·h")
    dir_.set_xlabel("Hora do dia")
    dir_.set_xticks(range(0, 25, 4))
    dir_.set_xlim(0, 24)
    dir_.set_ylim(22, 42)
    dir_.grid(alpha=0.3)
    dir_.legend(loc="upper left", fontsize="small")
 
    plt.tight_layout()
    os.makedirs(PASTA_GRAFICOS, exist_ok=True)
    plt.savefig(os.path.join(PASTA_GRAFICOS, "06_graus_hora.png"), dpi=150)
    plt.show()
 
 
if __name__ == "__main__":
    grafico_indice_ao_longo_do_dia()
    grafico_zoom_descontinuidade()
    tabela_taxa_como_limite(t=11)   # subida mais rápida
    tabela_taxa_como_limite(t=15)   # perto do pico, a curva já desacelera
    grafico_derivada_indice()
    grafico_regra_da_cadeia()
    tabela_erro_projecao()
    grafico_retas_tangentes()
    tabela_graus_hora()
    grafico_graus_hora()