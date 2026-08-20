# Devil's Advocate Workflow

## Propósito

El workflow Devil's Advocate argumenta **automáticamente EN CONTRA** de cada PR de estrategia. Su único mandato es encontrar debilidades, riesgos, y razones por las que la propuesta podría fallar.

## ¿Por qué?

- **Evitar groupthink**: Cuando todos están emocionados con una idea, nadie cuestiona
- **Confirmation bias**: Tendemos a buscar evidencia que confirme nuestras ideas
- **Trading especialmente vulnerable**: Las malas decisiones de trading cuestan dinero

## Configuración

### Secreto Requerido

El workflow requiere `DEVIL_API_KEY` configurado en los secretos del repositorio:

1. Ve a Settings → Secrets and variables → Actions
2. Añade un secreto llamado `DEVIL_API_KEY`
3. Usa una API key de Google AI Studio (Gemini)

### Obtener API Key

1. Ve a [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Crea una nueva API key
3. Copia la key al secreto del repositorio

## Cuándo se Activa

El workflow se activa en PRs que:

1. No están en draft
2. Tocan archivos en:
   - `src/executor/**`
   - `src/researcher/**`
   - `docs/LAB_*.md`
   - `strategies/**`
3. Y tienen label `strategy` O el título contiene `LAB_`, `executor`, o `researcher`

## Proceso de Revisión

1. **PR se abre/actualiza** → El diablo genera crítica
2. **Autor lee la crítica** → Obligatorio responder
3. **Respuesta documentada** → Explica por qué la crítica no aplica o qué se cambió
4. **Entonces** → El PR puede ser aprobado

## Reglas del Diablo

El modelo sigue estas reglas:

1. SIEMPRE argumenta en contra, nunca a favor
2. Es específico y técnico
3. Menciona riesgos de mercado, implementación, y comportamiento
4. Pregunta qué podría salir mal
5. Cuestiona supuestos implícitos
6. Es constructivo pero implacable

## Ejemplo de Uso

```markdown
## 👿 Abogado del Diablo

Esta estrategia de cruce de EMAs tiene varios problemas potenciales:

1. **Lag inherente**: Las EMAs son indicadores retrasados. Para cuando 
   detectas el cruce, el movimiento ya pasó.

2. **Whipsaws**: En mercados laterales, los cruces frecuentes generarán
   múltiples señales falsas consecutivas, destruyendo el capital.

3. **R:R fijo 2:1**: ¿Por qué 2:1? No hay justificación basada en datos.
   El mercado no respeta ratios arbitrarios.

...
```

## Respuesta Obligatoria

Antes de aprobar el PR, el autor debe responder a la crítica:

```markdown
> Lag inherente

Aceptado. Por eso añadimos confirmación de vela para reducir entradas prematuras.

> Whipsaws

El ATR floor previene operar en rangos estrechos donde los whipsaws son peores.

> R:R fijo

Es un punto de partida. El lab medirá si 2:1 es óptimo o necesita ajuste.
```

## Limitaciones

- El diablo no tiene contexto completo del mercado actual
- A veces las críticas son genéricas - ignorar las que no aplican
- No es un bloqueante automático, es información para tomar mejores decisiones
