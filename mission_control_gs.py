"""
=============================================================================
MISSION CONTROL AI — Sistema de Monitoramento Energético
=============================================================================
Disciplina : Soluções em Energias Renováveis e Sustentáveis
Plataforma : Python 3.x
Versão     : 1.0
=============================================================================
Descrição:
    Sistema de monitoramento energético para missão espacial experimental.
    Simula dados de geração fotovoltaica, consumo por módulo, balanço
    energético, eficiência operacional e geração automática de alertas
    com tomada de decisão autônoma.

Execução:
    python mission_control_ai.py

Requisitos:
    Python 3.8+  |  Sem dependências externas
=============================================================================
"""

import time
import random
import os
from datetime import datetime
from enum import Enum

# =============================================================================
# ENUMERAÇÕES
# =============================================================================

class NivelAlerta(Enum):
    INFO      = 0
    WARNING   = 1
    CRITICAL  = 2
    EMERGENCY = 3

class ModoOperacao(Enum):
    NORMAL    = "NORMAL"
    ECONOMY   = "ECONOMY"
    SAFE      = "SAFE"
    EMERGENCY = "EMERGENCY"

class StatusEnergia(Enum):
    SUPERAVIT   = "SUPERÁVIT"
    EQUILIBRADO = "EQUILIBRADO"
    DEFICIT     = "DÉFICIT"
    CRITICO     = "CRÍTICO"

# =============================================================================
# PARÂMETROS DE CONFIGURAÇÃO
# =============================================================================

# Thresholds de temperatura (°C)
TEMP_WARN_MAX  = 50.0
TEMP_CRIT_MAX  = 60.0
TEMP_CRIT_MIN  = 0.0

# Thresholds de luminosidade (0–100%)
LUX_ESCURIDAO  = 10    # %
LUX_SOLAR_PLENO = 80   # %

# Thresholds de vibração (eventos em janela de 5s)
VIB_WARN_COUNT = 2
VIB_CRIT_COUNT = 3

# Parâmetros energéticos (mW)
SOLAR_MAX_MW      = 500.0
GERACAO_MINIMA_MW = 10.0

# Consumo por módulo (mW)
CONSUMO_ARDUINO_MW = 250.0
CONSUMO_LCD_MW     = 300.0
CONSUMO_TMP36_MW   = 0.25
CONSUMO_LDR_MW     = 2.5
CONSUMO_LED_MW     = 68.0
CONSUMO_BASE_MW    = CONSUMO_ARDUINO_MW + CONSUMO_LCD_MW + CONSUMO_TMP36_MW + CONSUMO_LDR_MW

# Intervalos de ciclo (segundos)
CICLO_NORMAL_S  = 2.0
CICLO_ECONOMY_S = 5.0

# Histerese de retorno ao NORMAL (ciclos)
HISTERESE_CICLOS = 5

# Cores para terminal
COR = {
    "reset"  : "\033[0m",
    "verde"  : "\033[92m",
    "amarelo": "\033[93m",
    "vermelho": "\033[91m",
    "ciano"  : "\033[96m",
    "branco" : "\033[97m",
    "cinza"  : "\033[90m",
    "negrito": "\033[1m",
    "azul"   : "\033[94m",
}

# =============================================================================
# ESTRUTURA DE TELEMETRIA
# =============================================================================

class TelemetriaData:
    """Estrutura central de dados do sistema — todos os módulos leem e escrevem aqui."""

    def __init__(self):
        # Dados ambientais
        self.temperatura_C      = 25.0
        self.luminosidade_pct   = 50.0
        self.vibracao_eventos   = 0

        # Dados energéticos
        self.energia_geracao_mW  = 0.0
        self.energia_consumo_mW  = 0.0
        self.energia_balanco_mW  = 0.0
        self.energia_eficiencia  = 0.0
        self.energia_status      = StatusEnergia.EQUILIBRADO

        # Estado do sistema
        self.alerta_nivel        = NivelAlerta.INFO
        self.alerta_origem       = "SISTEMA"
        self.modo_operacao       = ModoOperacao.NORMAL
        self.timestamp           = datetime.now()
        self.ciclo               = 0

        # Controle de LEDs
        self.led_critico_ativo   = False
        self.led_normal_ativo    = False

# =============================================================================
# SIMULADOR DE SENSORES
# =============================================================================

class SimuladorSensores:
    """
    Simula leituras de sensores com variação realista.
    Em um sistema real, estes valores viriam do hardware (Arduino/ESP32).
    """

    def __init__(self):
        self._temp_base     = 25.0
        self._lux_base      = 50.0
        self._ciclo_interno = 0
        self._cenario       = "normal"
        self._cenario_timer = 0

    def definir_cenario(self, cenario: str):
        """Define um cenário de simulação específico."""
        self._cenario       = cenario
        self._cenario_timer = 0

    def ler(self) -> dict:
        """Retorna leituras simuladas dos três sensores."""
        self._ciclo_interno  += 1
        self._cenario_timer  += 1

        # ── Temperatura ─────────────────────────────────────────────────
        if self._cenario == "temp_alta":
            temp = 58.0 + random.uniform(-1, 3)
        elif self._cenario == "temp_critica":
            temp = 63.0 + random.uniform(-1, 2)
        elif self._cenario == "temp_fria":
            temp = -2.0 + random.uniform(-1, 2)
        else:
            # Variação natural com tendência senoidal
            variacao = 3.0 * (self._ciclo_interno % 20) / 20
            temp = self._temp_base + variacao + random.uniform(-0.5, 0.5)

        # ── Luminosidade ────────────────────────────────────────────────
        if self._cenario == "eclipse":
            lux = random.uniform(0, 8)
        elif self._cenario == "solar_pleno":
            lux = random.uniform(85, 100)
        else:
            # Variação natural gradual
            delta = random.uniform(-5, 5)
            self._lux_base = max(5, min(95, self._lux_base + delta))
            lux = self._lux_base + random.uniform(-2, 2)

        # ── Vibração ────────────────────────────────────────────────────
        if self._cenario == "vibracao_alta":
            vib = random.randint(3, 5)
        elif self._cenario == "vibracao_media":
            vib = random.randint(1, 3)
        else:
            # Vibrações ocasionais aleatórias
            vib = random.choices([0, 1, 2, 3], weights=[70, 20, 7, 3])[0]

        return {
            "temperatura_C"   : round(temp, 1),
            "luminosidade_pct": round(max(0, min(100, lux)), 1),
            "vibracao_eventos": vib
        }

# =============================================================================
# MÓDULO 1 — LEITURA DE SENSORES
# =============================================================================

def modulo_ler_sensores(telemetria: TelemetriaData, simulador: SimuladorSensores):
    """Coleta e atualiza os dados dos sensores na estrutura de telemetria."""
    leituras = simulador.ler()
    telemetria.temperatura_C    = leituras["temperatura_C"]
    telemetria.luminosidade_pct = leituras["luminosidade_pct"]
    telemetria.vibracao_eventos = leituras["vibracao_eventos"]
    telemetria.timestamp        = datetime.now()
    telemetria.ciclo           += 1

# =============================================================================
# MÓDULO 2 — SISTEMA DE ALERTAS
# =============================================================================

def modulo_alertas(telemetria: TelemetriaData):
    """Avalia thresholds e classifica o nível de alerta global."""
    nivel   = NivelAlerta.INFO
    origem  = "SISTEMA"
    criticos = 0

    t   = telemetria.temperatura_C
    lux = telemetria.luminosidade_pct
    vib = telemetria.vibracao_eventos

    # ── Temperatura ──────────────────────────────────────────────────────
    if t > TEMP_CRIT_MAX or t < TEMP_CRIT_MIN:
        nivel = NivelAlerta.CRITICAL
        origem = "TEMPERATURA"
        criticos += 1
    elif t > TEMP_WARN_MAX:
        if nivel.value < NivelAlerta.WARNING.value:
            nivel = NivelAlerta.WARNING
            origem = "TEMPERATURA"

    # ── Luminosidade ─────────────────────────────────────────────────────
    if lux < LUX_ESCURIDAO:
        if nivel.value < NivelAlerta.WARNING.value:
            nivel = NivelAlerta.WARNING
            origem = "LUZ BAIXA"
    elif lux > LUX_SOLAR_PLENO:
        if nivel.value < NivelAlerta.WARNING.value:
            nivel = NivelAlerta.WARNING
            origem = "LUZ ALTA"

    # ── Vibração ─────────────────────────────────────────────────────────
    if vib >= VIB_CRIT_COUNT:
        if nivel.value < NivelAlerta.CRITICAL.value:
            nivel = NivelAlerta.CRITICAL
            origem = "VIBRAÇÃO"
        criticos += 1
    elif vib >= VIB_WARN_COUNT:
        if nivel.value < NivelAlerta.WARNING.value:
            nivel = NivelAlerta.WARNING
            origem = "VIBRAÇÃO"

    # ── Energia ──────────────────────────────────────────────────────────
    if telemetria.energia_status == StatusEnergia.CRITICO:
        if nivel.value < NivelAlerta.CRITICAL.value:
            nivel = NivelAlerta.CRITICAL
            origem = "ENERGIA"
        criticos += 1
    elif telemetria.energia_status == StatusEnergia.DEFICIT:
        if nivel.value < NivelAlerta.WARNING.value:
            nivel = NivelAlerta.WARNING
            origem = "ENERGIA"

    # ── EMERGENCY ────────────────────────────────────────────────────────
    if criticos >= 2:
        nivel  = NivelAlerta.EMERGENCY
        origem = "MÚLTIPLOS"

    telemetria.alerta_nivel  = nivel
    telemetria.alerta_origem = origem

# =============================================================================
# MÓDULO 3 — DECISÃO AUTÔNOMA (FSM)
# =============================================================================

def modulo_decisao(telemetria: TelemetriaData, contador_histerese: list):
    """
    Máquina de estados finitos com histerese de retorno ao modo NORMAL.
    contador_histerese é uma lista de um elemento [int] para permitir mutação.
    """
    if telemetria.alerta_nivel == NivelAlerta.EMERGENCY:
        novo_modo = ModoOperacao.EMERGENCY
    elif telemetria.energia_status == StatusEnergia.CRITICO:
        novo_modo = ModoOperacao.ECONOMY
    elif telemetria.alerta_nivel == NivelAlerta.CRITICAL:
        novo_modo = ModoOperacao.SAFE
    else:
        novo_modo = ModoOperacao.NORMAL

    # Histerese: exige HISTERESE_CICLOS ciclos estáveis para retornar ao NORMAL
    if novo_modo == ModoOperacao.NORMAL and telemetria.modo_operacao != ModoOperacao.NORMAL:
        contador_histerese[0] += 1
        if contador_histerese[0] < HISTERESE_CICLOS:
            return  # Ainda aguardando estabilização
        contador_histerese[0] = 0
    elif novo_modo != ModoOperacao.NORMAL:
        contador_histerese[0] = 0  # Cancela estabilização se piorou

    telemetria.modo_operacao = novo_modo

# =============================================================================
# MÓDULO 4 — ATUALIZAÇÃO DE LEDS
# =============================================================================

def modulo_atualizar_leds(telemetria: TelemetriaData):
    """Determina estado dos LEDs indicadores conforme nível de alerta."""
    telemetria.led_critico_ativo = telemetria.alerta_nivel in (
        NivelAlerta.CRITICAL, NivelAlerta.EMERGENCY
    )
    telemetria.led_normal_ativo = (
        telemetria.alerta_nivel == NivelAlerta.INFO and
        telemetria.modo_operacao == ModoOperacao.NORMAL
    )

# =============================================================================
# MÓDULO 5 — GESTÃO ENERGÉTICA
# =============================================================================

def modulo_energia(telemetria: TelemetriaData):
    """
    Calcula geração fotovoltaica, consumo, balanço e eficiência operacional.
    A luminosidade (%) é o proxy de irradiância solar.
    """
    # ── Geração fotovoltaica (proxy via luminosidade) ─────────────────────
    geracao = (telemetria.luminosidade_pct / 100.0) * SOLAR_MAX_MW
    if geracao < GERACAO_MINIMA_MW:
        geracao = GERACAO_MINIMA_MW
    telemetria.energia_geracao_mW = round(geracao, 2)

    # ── Consumo dinâmico por módulo ───────────────────────────────────────
    consumo = CONSUMO_BASE_MW
    if telemetria.led_critico_ativo:
        consumo += CONSUMO_LED_MW
    if telemetria.led_normal_ativo:
        consumo += CONSUMO_LED_MW
    telemetria.energia_consumo_mW = round(consumo, 2)

    # ── Balanço e eficiência ──────────────────────────────────────────────
    balanco = geracao - consumo
    telemetria.energia_balanco_mW  = round(balanco, 2)
    telemetria.energia_eficiencia  = round(min(100.0, (geracao / consumo) * 100), 1)

    # ── Classificação do status energético ───────────────────────────────
    if   balanco >= 100.0:  telemetria.energia_status = StatusEnergia.SUPERAVIT
    elif balanco >=   0.0:  telemetria.energia_status = StatusEnergia.EQUILIBRADO
    elif balanco >= -50.0:  telemetria.energia_status = StatusEnergia.DEFICIT
    else:                   telemetria.energia_status = StatusEnergia.CRITICO

# =============================================================================
# MÓDULO 6 — DISPLAY (Terminal)
# =============================================================================

def limpar_terminal():
    os.system('cls' if os.name == 'nt' else 'clear')

def cor_alerta(nivel: NivelAlerta) -> str:
    return {
        NivelAlerta.INFO:      COR["verde"],
        NivelAlerta.WARNING:   COR["amarelo"],
        NivelAlerta.CRITICAL:  COR["vermelho"],
        NivelAlerta.EMERGENCY: COR["vermelho"] + COR["negrito"],
    }.get(nivel, COR["reset"])

def cor_energia(status: StatusEnergia) -> str:
    return {
        StatusEnergia.SUPERAVIT:   COR["verde"],
        StatusEnergia.EQUILIBRADO: COR["ciano"],
        StatusEnergia.DEFICIT:     COR["amarelo"],
        StatusEnergia.CRITICO:     COR["vermelho"],
    }.get(status, COR["reset"])

def modulo_display(telemetria: TelemetriaData):
    """Exibe o painel de monitoramento no terminal com formatação visual."""
    limpar_terminal()
    R = COR["reset"]
    B = COR["negrito"]
    C = COR["ciano"]
    G = COR["verde"]
    Y = COR["amarelo"]
    W = COR["branco"]
    GR = COR["cinza"]

    ca = cor_alerta(telemetria.alerta_nivel)
    ce = cor_energia(telemetria.energia_status)

    linha = "═" * 60

    print(f"\n{C}{B}{'═'*60}{R}")
    print(f"{C}{B}   🛸  MISSION CONTROL AI — Painel de Monitoramento{R}")
    print(f"{C}{B}   Soluções em Energias Renováveis e Sustentáveis{R}")
    print(f"{C}{B}{'═'*60}{R}\n")

    # ── Timestamp e ciclo ─────────────────────────────────────────────────
    ts = telemetria.timestamp.strftime("%Y-%m-%d %H:%M:%S")
    print(f"  {GR}Ciclo #{telemetria.ciclo:04d}   {ts}{R}")
    print(f"  {GR}Modo: {B}{telemetria.modo_operacao.value}{R}", end="   ")
    led_v = f"{G}● NORMAL{R}" if telemetria.led_normal_ativo else f"{GR}○{R}"
    led_r = f"{COR['vermelho']}● ALERTA{R}" if telemetria.led_critico_ativo else f"{GR}○{R}"
    print(f"LED Verde: {led_v}   LED Vermelho: {led_r}")
    print()

    # ── Sensores Ambientais ───────────────────────────────────────────────
    print(f"  {B}{'─'*56}{R}")
    print(f"  {B}  SENSORES AMBIENTAIS{R}")
    print(f"  {B}{'─'*56}{R}")

    # Temperatura
    t = telemetria.temperatura_C
    ct = COR["vermelho"] if (t > TEMP_CRIT_MAX or t < TEMP_CRIT_MIN) \
         else COR["amarelo"] if t > TEMP_WARN_MAX \
         else COR["verde"]
    barra_t = int((t + 40) / 1.65)
    barra_t = max(0, min(60, barra_t))
    print(f"  🌡️  Temperatura   {ct}{B}{t:+6.1f} °C{R}  [{ct}{'█'*barra_t}{'░'*(60-barra_t)}{R}]")

    # Luminosidade
    lux = telemetria.luminosidade_pct
    cl = COR["amarelo"] if lux < LUX_ESCURIDAO or lux > LUX_SOLAR_PLENO else COR["verde"]
    barra_l = int(lux * 0.6)
    print(f"  ☀️  Luminosidade  {cl}{B}{lux:6.1f} %{R}    [{cl}{'█'*barra_l}{'░'*(60-barra_l)}{R}]")

    # Vibração
    vib = telemetria.vibracao_eventos
    cv = COR["vermelho"] if vib >= VIB_CRIT_COUNT \
         else COR["amarelo"] if vib >= VIB_WARN_COUNT \
         else COR["verde"]
    print(f"  📳  Vibração      {cv}{B}{vib:6d} eventos{R}  {'⚡'*vib}")
    print()

    # ── Painel Energético ─────────────────────────────────────────────────
    print(f"  {B}{'─'*56}{R}")
    print(f"  {B}  PAINEL ENERGÉTICO{R}")
    print(f"  {B}{'─'*56}{R}")

    g  = telemetria.energia_geracao_mW
    co = telemetria.energia_consumo_mW
    ba = telemetria.energia_balanco_mW
    ef = telemetria.energia_eficiencia

    barra_g = int((g / SOLAR_MAX_MW) * 50)
    barra_e = int(ef * 0.5)

    print(f"  ⚡  Geração       {G}{B}{g:7.1f} mW{R}   [{G}{'█'*barra_g}{'░'*(50-barra_g)}{R}]")
    print(f"  🔌  Consumo       {W}{B}{co:7.1f} mW{R}")

    sinal = "+" if ba >= 0 else ""
    cb = COR["verde"] if ba >= 100 else COR["ciano"] if ba >= 0 \
         else COR["amarelo"] if ba >= -50 else COR["vermelho"]
    print(f"  ⚖️  Balanço       {cb}{B}{sinal}{ba:6.1f} mW{R}")

    barra_e = max(0, min(50, barra_e))
    print(f"  📊  Eficiência    {ce}{B}{ef:6.1f} %{R}    [{ce}{'█'*barra_e}{'░'*(50-barra_e)}{R}]")

    print(f"\n  Status Energético: {ce}{B}{telemetria.energia_status.value}{R}")
    print()

    # ── Status de Alerta ──────────────────────────────────────────────────
    print(f"  {B}{'─'*56}{R}")
    icone = {"INFO": "✅", "WARNING": "⚠️", "CRITICAL": "🚨", "EMERGENCY": "🆘"}
    nome_alerta = telemetria.alerta_nivel.name
    print(f"  {icone.get(nome_alerta,'❓')}  Alerta: {ca}{B}{nome_alerta}{R}", end="")
    if telemetria.alerta_nivel != NivelAlerta.INFO:
        print(f"   Origem: {ca}{telemetria.alerta_origem}{R}", end="")
    print()

    if telemetria.alerta_nivel == NivelAlerta.EMERGENCY:
        print(f"\n  {COR['vermelho']}{B}!!! EMERGÊNCIA — MÚLTIPLAS FALHAS SIMULTÂNEAS !!!{R}")
    elif telemetria.alerta_nivel == NivelAlerta.CRITICAL:
        print(f"\n  {COR['vermelho']}{B}⚠  CONDIÇÃO CRÍTICA DETECTADA — {telemetria.alerta_origem}{R}")

    print(f"\n{C}{'═'*60}{R}")
    print(f"{GR}  Pressione Ctrl+C para encerrar a simulação{R}\n")

# =============================================================================
# MÓDULO 7 — TELEMETRIA (LOG)
# =============================================================================

def modulo_telemetria(telemetria: TelemetriaData, arquivo_log):
    """Registra linha de telemetria estruturada no arquivo de log."""
    prefixo = {
        NivelAlerta.INFO:      "[INFO]    ",
        NivelAlerta.WARNING:   "[WARN]    ",
        NivelAlerta.CRITICAL:  "[CRIT]    ",
        NivelAlerta.EMERGENCY: "[EMERG]   ",
    }[telemetria.alerta_nivel]

    ts   = telemetria.timestamp.strftime("%Y-%m-%d %H:%M:%S")
    orig = f" | ORIGEM:{telemetria.alerta_origem}" if telemetria.alerta_nivel != NivelAlerta.INFO else ""

    linha = (
        f"{prefixo} {ts} | "
        f"CICLO:{telemetria.ciclo:04d} | "
        f"T:{telemetria.temperatura_C:+.1f}C | "
        f"LUX:{telemetria.luminosidade_pct:.1f}% | "
        f"VIB:{telemetria.vibracao_eventos} | "
        f"GER:{telemetria.energia_geracao_mW:.1f}mW | "
        f"CONS:{telemetria.energia_consumo_mW:.1f}mW | "
        f"BAL:{telemetria.energia_balanco_mW:+.1f}mW | "
        f"EFI:{telemetria.energia_eficiencia:.1f}% | "
        f"EN:{telemetria.energia_status.value} | "
        f"MODO:{telemetria.modo_operacao.value}"
        f"{orig}"
    )

    arquivo_log.write(linha + "\n")
    arquivo_log.flush()

# =============================================================================
# GERENCIADOR DE CENÁRIOS DE SIMULAÇÃO
# =============================================================================

def proximo_cenario(ciclo: int, simulador: SimuladorSensores):
    """
    Alterna entre cenários de simulação para demonstrar
    todas as capacidades do sistema ao longo da execução.
    """
    cenarios = [
        (5,  "normal",         "Operação Normal"),
        (10, "eclipse",        "Eclipse Solar — geração baixa"),
        (15, "normal",         "Operação Normal"),
        (20, "temp_alta",      "Temperatura Alta — WARNING"),
        (25, "temp_critica",   "Temperatura Crítica — CRITICAL"),
        (30, "normal",         "Operação Normal — estabilização"),
        (35, "vibracao_media", "Vibração Moderada — WARNING"),
        (40, "vibracao_alta",  "Vibração Severa — CRITICAL"),
        (45, "temp_critica",   "EMERGÊNCIA — Temperatura + Vibração"),
        (50, "normal",         "Retorno à Operação Normal"),
    ]

    for limite, cenario, descricao in cenarios:
        if ciclo == limite:
            simulador.definir_cenario(cenario)
            return descricao

    if ciclo > 50:
        simulador.definir_cenario("normal")

    return None

# =============================================================================
# LOOP PRINCIPAL
# =============================================================================

def main():
    print("\033[92m\033[1m")
    print("  ╔══════════════════════════════════════════════════════╗")
    print("  ║          MISSION CONTROL AI — Iniciando...           ║")
    print("  ║  Soluções em Energias Renováveis e Sustentáveis      ║")
    print("  ╚══════════════════════════════════════════════════════╝")
    print("\033[0m")
    time.sleep(1.5)

    telemetria          = TelemetriaData()
    simulador           = SimuladorSensores()
    contador_histerese  = [0]

    # Abre arquivo de log de telemetria
    nome_log = f"telemetria_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    arquivo_log = open(nome_log, "w", encoding="utf-8")
    arquivo_log.write("=" * 100 + "\n")
    arquivo_log.write("MISSION CONTROL AI — Log de Telemetria Energética\n")
    arquivo_log.write(f"Início: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    arquivo_log.write("=" * 100 + "\n\n")

    try:
        while True:
            # Verifica troca de cenário
            descricao_cenario = proximo_cenario(telemetria.ciclo, simulador)

            # Determina intervalo conforme modo
            intervalo = CICLO_ECONOMY_S \
                if telemetria.modo_operacao in (ModoOperacao.ECONOMY, ModoOperacao.EMERGENCY) \
                else CICLO_NORMAL_S

            # ── Ciclo de execução ──────────────────────────────────────────
            modulo_ler_sensores(telemetria, simulador)   # 1. Lê sensores
            modulo_alertas(telemetria)                   # 2. Classifica alertas
            modulo_decisao(telemetria, contador_histerese)  # 3. FSM
            modulo_atualizar_leds(telemetria)            # 4. LEDs
            modulo_energia(telemetria)                   # 5. Balanço energético
            modulo_display(telemetria)                   # 6. Painel terminal

            # Exibe mudança de cenário se houver
            if descricao_cenario:
                print(f"  {COR['ciano']}📡 Cenário: {descricao_cenario}{COR['reset']}\n")

            modulo_telemetria(telemetria, arquivo_log)   # 7. Log

            time.sleep(intervalo)

    except KeyboardInterrupt:
        arquivo_log.write(f"\nEncerrado pelo usuário em {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        arquivo_log.close()
        print(f"\n\n  {COR['ciano']}Simulação encerrada. Log salvo em: {nome_log}{COR['reset']}\n")

# =============================================================================
# ENTRADA
# =============================================================================

if __name__ == "__main__":
    main()
