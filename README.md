# 🌱 Mission Control AI — Energias Renováveis

> Sistema de monitoramento energético inteligente para missão espacial experimental — Python + Geração Fotovoltaica Simulada

<br>

[![Python](https://img.shields.io/badge/Python-3.8+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![Version](https://img.shields.io/badge/Versão-1.0-success?style=for-the-badge)]()
[![ODS7](https://img.shields.io/badge/ODS-7%20Energia%20Limpa-green?style=for-the-badge)](https://sdgs.un.org/goals/goal7)
[![ODS9](https://img.shields.io/badge/ODS-9%20Inovação-orange?style=for-the-badge)](https://sdgs.un.org/goals/goal9)

<br>

---

## 📋 Índice

- [Introdução](#-introdução)
- [Objetivos](#-objetivos)
- [Como Funciona](#-como-funciona)
- [Modelo Energético](#-modelo-energético)
- [Sistema de Alertas](#-sistema-de-alertas)
- [Tomada de Decisão Automática](#-tomada-de-decisão-automática)
- [Sustentabilidade](#-sustentabilidade)
- [Como Executar](#-como-executar)
- [Estrutura do Repositório](#-estrutura-do-repositório)

---

## 🚀 Introdução

O **Mission Control AI** é um sistema de monitoramento energético inteligente desenvolvido em Python para a disciplina de **Soluções em Energias Renováveis e Sustentáveis** da FIAP.

O sistema simula o gerenciamento de energia de uma missão espacial experimental, aplicando os mesmos princípios utilizados no EPS (Electrical Power Subsystem) de satélites reais — como os da NASA e ESA — em escala embarcada e educacional.

---

## 🎯 Objetivos

- Monitorar geração fotovoltaica simulada via sensor de irradiância
- Calcular consumo energético por módulo ativo em tempo real
- Calcular balanço e eficiência operacional continuamente
- Gerar alertas automáticos em 4 níveis de criticidade
- Tomar decisões autônomas de modo operacional
- Registrar telemetria energética em arquivo de log

---

## ⚙️ Como Funciona

O sistema **não usa hardware físico** — todos os dados são simulados pelo próprio Python. O `SimuladorSensores` gera valores realistas de temperatura, luminosidade e vibração, e alterna automaticamente entre 10 cenários durante a execução:

| Ciclo | Cenário | Evento |
|---|---|---|
| 5 | Normal | Operação padrão |
| 10 | Eclipse | Geração fotovoltaica cai |
| 20 | Temperatura alta | Alerta WARNING |
| 25 | Temperatura crítica | Alerta CRITICAL |
| 40 | Vibração severa | Alerta CRITICAL |
| 45 | Múltiplas falhas | EMERGENCY |
| 50 | Retorno ao normal | Estabilização |

---

## ⚡ Modelo Energético

```
Geração (mW)  = (Luminosidade % / 100) × 500 mW
                mínimo garantido: 10 mW (bateria residual)

Consumo (mW)  = Arduino(250) + LCD(300) + TMP36(0.25) + LDR(2.5)
                + LED_vermelho(68) se ativo
                + LED_verde(68)    se ativo

Balanço (mW)  = Geração − Consumo
Eficiência(%) = (Geração / Consumo) × 100  [teto: 100%]
```

### Status Energético

| Status | Condição |
|---|---|
| SUPERÁVIT | Balanço ≥ +100 mW |
| EQUILIBRADO | Balanço 0 a +99 mW |
| DÉFICIT | Balanço −50 mW a 0 |
| CRÍTICO | Balanço < −50 mW |

---

## 🚨 Sistema de Alertas

| Nível | Condição | Comportamento |
|---|---|---|
| INFO | Tudo normal | Painel verde no terminal |
| WARNING | Parâmetro próximo ao limite | Painel amarelo |
| CRITICAL | Parâmetro fora do limite | Painel vermelho |
| EMERGENCY | 2+ CRITICAL simultâneos | Painel vermelho piscante |

---

## 🤖 Tomada de Decisão Automática

O sistema implementa uma **máquina de estados finitos** com 4 modos:

| Modo | Ativação | Ação |
|---|---|---|
| NORMAL | Sem alertas | Ciclo 2s, operação plena |
| ECONOMY | Energia CRÍTICO | Ciclo 5s, reduz processamento |
| SAFE | 1 CRITICAL | Ciclo 2s, prioriza alertas |
| EMERGENCY | 2+ CRITICAL | Ciclo 5s, modo sobrevivência |

---

## 🌍 Sustentabilidade

O projeto está alinhado com os ODS da Agenda 2030:

- **ODS 7** — Energia Limpa e Acessível: modelagem de geração fotovoltaica como fonte primária
- **ODS 9** — Indústria e Inovação: sistema IoT de gestão energética inteligente
- **ODS 13** — Ação Climática: eficiência energética e load shedding automático

---

## ▶️ Como Executar

**Requisitos:** Python 3.8+ — sem dependências externas

```bash
python mission_control_ai.py
```

O sistema vai:
1. Exibir o painel de monitoramento no terminal com cores
2. Alternar automaticamente entre cenários de simulação
3. Salvar um arquivo `.log` com toda a telemetria

---

## 📁 Estrutura do Repositório

```
mission-control-ai-energia/
│
├── 📄 README.md
├── 📄 mission_control_ai.py
```

---

## 👨‍💻 Autor

Desenvolvido como projeto acadêmico — FIAP 2026
Disciplina: **Soluções em Energias Renováveis e Sustentáveis**

---

<div align="center">

**Mission Control AI v1.0** · Python · FIAP 2026

*"Os princípios que governam satélites em órbita são os mesmos que governam microrredes na Terra."*

</div>
