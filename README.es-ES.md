

# StataFlow

**Un kit de herramientas de econométrica en Python diseñado para reproducir resultados de estimación de Stata 17 con validación a nivel de campo.**

[简体中文](README.zh-CN.md)

[![PyPI version](https://img.shields.io/pypi/v/stataflow)](https://pypi.org/project/stataflow/)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)

---

```python
from stataflow.compat.stata import reghdfe

result = reghdfe(
    df,
    y="lwage",
    x=["exper", "edu"],
    absorb="firm_id year_id",
    vce="cluster",
    cluster="firm_id",
)
result.display()
```

---

## Por qué StataFlow

StataFlow está dirigido a investigadores que desean flujos de trabajo en Python sin renunciar a las convenciones empíricas en las que confían en Stata. El proyecto no es una biblioteca de estadísticas genérica: las capacidades públicas están respaldadas por casos sintéticos, casos de datos reales públicos y comparaciones con Stata 17 a nivel de campo.

La versión de desarrollo actual es **1.3.0**, que cubre 14 comandos al estilo de Stata.

## Características

- **14 comandos de estimación en Python**: `regress`, `xtreg_fe`, `areg`, `reghdfe`, `ivregress_2sls`, `ivreghdfe`, `logit`, `probit`, `poisson`, `ppmlhdfe`, `did_imputation`, `eventstudyinteract`, `csdid` y `rdrobust`. El complemento exportado `rdplot` es una ayuda y no se cuenta como un comando de estimación.
- **Dos capas de API**: una capa de comandos compatible con Stata (`stataflow.compat.stata`) y una capa de estimadores nativa de Python (`stataflow.estimators`).
- **Salida estilo Stata consciente de los comandos**: `result.display()` imprime una tabla de resultados completa y adaptativa con las estadísticas y diagnósticos relevantes para cada comando; los cuadernos reciben el mismo contenido como HTML escapado.
- **Efectos fijos de alta dimensión**: absorción MAP para diseños FE grandes, flujos de trabajo con múltiples FE, manejo de singularidades, pendientes individuales y rutas de VCE conscientes de los clústeres.
- **Variables instrumentales**: 2SLS, GMM2S, LIML, Fuller/clase-k, diagnósticos de primera etapa, pruebas de instrumentos débiles y pruebas de sobreidentificación.
- **Modelos binarios, de recuento y PPML**: Logit, Probit, Poisson y PPML-HDFE con estimadores de covarianza robustos y en clústeres.
- **Inferencia causal**: Imputación de DID de BJS, interacciones de `event-study` de Sun-Abraham, DID de Callaway-Sant'Anna y discontinuidad en la regresión nítida/difusa.
- **Subconjuntos de sintaxis compatibles con Stata**: variables factor, soporte de pesos analíticos específico para comandos, múltiples efectos fijos, opciones comunes de VCE y rechazo estricto de parámetros no compatibles.
- **Desarrollo basado en validación**: los comandos públicos están respaldados por evidencia de comparación con Stata 17 a nivel de campo.

## Instalación

```bash
pip install StataFlow
```

Se requiere Python 3.10, 3.11 o 3.12. Las dependencias principales son NumPy, pandas, SciPy, scikit-learn y PyYAML.

## Inicio rápido

### API compatible con Stata

```python
from stataflow.compat.stata import regress, reghdfe, logit, ivregress_2sls, ppmlhdfe

# OLS with robust standard errors
result = regress(df, y="wage", x=["edu", "exper"], vce="robust")
result.display()

# High-dimensional fixed effects
result = reghdfe(
    df,
    y="wage",
    x=["edu", "exper"],
    absorb="firm_id year_id",
    vce="cluster",
    cluster="industry",
)

# Logit
result = logit(df, y="inlf", x=["nwifeinc", "educ", "exper"])
result.display()

# 2SLS with robust VCE
result = ivregress_2sls(
    df,
    y="lwage",
    x_exog=["educ"],
    x_endog=["exper"],
    instruments=["age", "kidslt6"],
    vce="robust",
)

# PPML with high-dimensional fixed effects
result = ppmlhdfe(
    df,
    y="trade",
    x=["lndist", "contig", "fta"],
    absorb=["exporter", "importer", "year"],
    vce="cluster",
    cluster="exporter",
)
```

### API nativa de Python

```python
from stataflow import OLS, AbsorbingOLS, Logit

model = OLS(data=df, y="wage", x=["edu", "exper"])
result = model.fit(vce="robust")
result.display()
```

### Trabajando con resultados

```python
result.display()                         # Full output with 95% CI
result.display(detail="compact")        # Header, coefficients, core fit
result.display(show_ci=False)           # Hide confidence intervals
text = result.summary(width=100)        # Return the same table as text
html = result.to_html()                 # Escaped HTML for reports/notebooks
```

## Modelos soportados

| Familia | Disponible a través de | Estimadores y VCE |
|--------|---------------|--------------------|
| Lineal | `regress`, `areg`, `xtreg_fe`, `reghdfe` | MCO con `ols`, `robust` (HC1) y agrupamiento específico del comando; `reghdfe` también admite `dkraay` HAC para paneles |
| IV | `ivregress_2sls`, `ivreghdfe` | 2SLS, GMM2S, LIML, Fuller/clase-k, diagnósticos de primera etapa, pruebas de IV débiles |
| Binario / Recuento | `logit`, `probit`, `poisson` | Verosimilitud máxima con VCE `ols`, `robust` y `cluster` |
| PPML + HDFE | `ppmlhdfe` | IRLS con efectos fijos, compensación/exposición, verificaciones de separación, `eform` y tipos de predicción comunes |
| DID | `did_imputation`, `csdid`, `eventstudyinteract` | Imputación BJS, Callaway-Sant'Anna y estimadores IW de Sun-Abraham |
| RD | `rdrobust` | RD nítida/difusa, selectores de ancho de banda MSE/CER, covariables, ponderaciones, puntos de masa y VCE en clústeres/nncluster |

Consulta la [Matriz de soporte de comandos](docs/command-support-matrix/README.md) y los [Problemas conocidos](docs/release/known-issues.md) para conocer los límites exactos de soporte.

## Validación

El alcance de la versión de julio de 2026 está congelado a los casos resumidos a continuación. La desviación relativa es `|Python - Stata| / max(|Stata|, 1e-15)`.

| Familia | Comandos cubiertos | Comparaciones con Stata 17 | Desviación máxima del coeficiente | Desviación máxima del EE |
|---|---|---:|---:|---:|
| Lineal / EF | `regress`, `areg`, `xtreg_fe`, `reghdfe` | 18/18 | 2.48e-7 | 2.25e-7 |
| IV | `ivregress_2sls`, `ivreghdfe` | 5/5 | 1.16e-8 | 3.74e-8 |
| Binario / recuento | `logit`, `probit`, `poisson`, `ppmlhdfe` | 12/12 | 1.33e-7 | 8.42e-8 |
| DID | `did_imputation`, `csdid`, `eventstudyinteract` | 2/2 + 1 verificación funcional | 8.13e-8 | 5.13e-8 |
| RD | `rdrobust` | 3/3 | 9.23e-8 | 2.96e-8 |
| **Total** | **14 comandos de estimación públicos** | **40/40** | **2.48e-7** | **2.25e-7** |

Verificaciones completas de validación local de Stata: `856 superadas, 12 omitidas`. La suite pública e independiente pasa `10/10` casos de validación reproducibles con Stata 17. Los valores anteriores se almacenan en [`evidence-summary.json`](research/results/validation/evidence-summary.json).

## Documentación

- [Guía de usuario](docs/USER_GUIDE.md) ([中文](docs/USER_GUIDE.zh-CN.md))
- [Libro de recetas](docs/cookbook.md) ([中文](docs/cookbook.zh-CN.md))
- [Ejemplos](examples/) — nueve scripts de demostración deterministas que cubren los 14 comandos públicos; no se requiere red ni Stata local
- [Evidencia de validación (JSON)](research/results/validation/evidence-summary.json)
- [Evidencia de validación (legible)](research/results/validation/evidence-summary.md)
- [Registro de cambios](CHANGELOG.md)

## Ejecución de pruebas

```bash
# Unit and integration tests
pytest tests/ -v

# Reproducible Stata validation cases (require local Stata 17)
pytest tests/stata_validation/ -v -s
```

## Comunidad

- [Guía de contribución](CONTRIBUTING.md) — flujo de trabajo de desarrollo, requisitos de prueba y verificaciones de PR
- [Política de seguridad](SECURITY.md) — versiones compatibles y reporte privado de vulnerabilidades
- [Código de conducta](CODE_OF_CONDUCT.md)

## Licencia

Este proyecto está licenciado bajo la Licencia MIT. Consulta [LICENSE](LICENSE) para más detalles.
