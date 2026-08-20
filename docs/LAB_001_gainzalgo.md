# LAB_001: GainzAlgo - Candidato 1 del Laboratorio

## Ficha Técnica

| Campo | Valor |
|-------|-------|
| **ID** | LAB_001 |
| **Nombre** | GainzAlgo |
| **Tipo** | Casero |
| **Fecha registro** | 2026-08-20 |
| **Arnés** | #13 (T1 completo) |

## Descripción

Estrategia de cruce de EMAs con confirmación de vela y gestión de riesgo fija 2:1.

### Componentes

1. **EMA Rápida (9 periodos)** - Detecta momentum a corto plazo
2. **EMA Lenta (21 periodos)** - Define la tendencia
3. **Confirmación de vela** - El cierre debe confirmar la dirección del cruce
4. **TP/SL 2:1** - Take Profit a 2x el riesgo, Stop Loss basado en ATR

### Reglas de Entrada

| Señal | Condición |
|-------|-----------|
| **LONG** | EMA9 cruza por encima de EMA21 AND vela cierra verde |
| **SHORT** | EMA9 cruza por debajo de EMA21 AND vela cierra roja |

### Reglas de Salida

- **Take Profit**: 2R (el doble de la distancia al Stop Loss)
- **Stop Loss**: 1.5 × ATR(14)
- **Señal opuesta**: Cierre inmediato si se genera señal contraria

### Gestión de Riesgo

- Riesgo por operación: 1% del capital
- Ratio recompensa/riesgo: 2:1 fijo
- Sin apalancamiento

---

## Pre-Registro (Protocolo Anti-Sobreajuste)

> **IMPORTANTE**: Este registro se hace ANTES de correr el backtest.
> Predecir el resultado evita sesgo de confirmación post-hoc.

### Predicción Pre-Registro

```
Predicción: SUSPENDE T1
Fecha: 2026-08-20
Razonamiento: Cruces de EMA son indicadores retrasados que generan 
              whipsaws frecuentes en mercados laterales. La confirmación 
              de vela reduce señales falsas pero no elimina el problema 
              fundamental. Esperamos win rate ~35-40% insuficiente para 
              superar los umbrales T1 del arnés.
```

---

## Ejecución del Test

**Arnés**: #13  
**Tier**: T1 (completo)  
**Estado**: Pendiente de ejecución

### Comandos

```bash
# Cuando el arnés #13 esté disponible:
python -m harness run --candidate LAB_001 --tier T1
```

---

## Veredicto

> **Nota**: Completar tras la ejecución del arnés.

| Métrica | Umbral T1 | Resultado | ¿Pasa? |
|---------|-----------|-----------|--------|
| Win Rate | ≥40% | - | - |
| Profit Factor | ≥1.2 | - | - |
| Max Drawdown | ≤15% | - | - |
| Sharpe Ratio | ≥0.5 | - | - |
| Trades/Mes | ≥5 | - | - |

### Resultado Final

```
Estado: PENDIENTE
Fecha ejecución: -
Veredicto: -
```

### Análisis Post-Mortem

_(Completar después de la ejecución, gane o pierda)_

---

## Lecciones

_(Documentar insights del test, independientemente del resultado)_

---

## Referencias

- Implementación: `src/executor/gainzalgo.py`
- Issue: Laboratorio · Candidato 1: GainzAlgo casero
- Arnés: `#13` en main
