# Skill lab-protocol: TODO

## Estado: Pendiente

Este skill se creará cuando el laboratorio tenga **2-3 candidatos corridos**.

## Instrucciones

Cuando se cumpla la condición:

1. Pedir a **Claude (Cowork)** que escriba el skill
2. El skill debe incluir el **protocolo anti-sobreajuste**
3. Documentar basándose en la experiencia de LAB_001, LAB_002, LAB_003

## Protocolo Anti-Sobreajuste

El skill debe cubrir:

### 1. Pre-Registro Obligatorio
- Predicción del resultado ANTES de correr el backtest
- Fecha y razonamiento documentados
- Evita sesgo de confirmación post-hoc

### 2. Umbrales Fijos
- Los umbrales T1/T2 se definen ANTES de correr
- No se ajustan después de ver resultados
- Estado absorbente: una vez que suspendes, suspendes

### 3. Out-of-Sample Testing
- Separación temporal de datos
- Nunca optimizar en datos de validación
- Walk-forward si aplica

### 4. Regla del Estado Absorbente
- Un candidato que suspende un tier NO se recupera
- No hay "segunda oportunidad" sin cambios estructurales
- Cambios cosméticos no cuentan como nuevo candidato

### 5. Documentación Win-or-Lose
- El veredicto se documenta SIEMPRE
- Gane o pierda, se escribe el post-mortem
- Las lecciones se registran para futuros candidatos

## Candidatos Actuales

| ID | Nombre | Estado | Predicción | Resultado |
|----|--------|--------|------------|-----------|
| LAB_001 | GainzAlgo | Registrado | SUSPENDE T1 | Pendiente |
| LAB_002 | - | - | - | - |
| LAB_003 | - | - | - | - |

## Trigger

Cuando la tabla tenga 2-3 candidatos con resultado (no pendiente):

```bash
# Solicitar a Claude (Cowork):
"Escribe el skill lab-protocol basándote en la experiencia de LAB_001-003.
 Incluye el protocolo anti-sobreajuste completo."
```

---

_Nota: Este archivo sirve como recordatorio. El skill real será creado por Claude (Cowork)._
