cat > README.md <<'EOF'
# VIGÍA Mercados

Sistema autónomo de vigilancia y análisis de mercados mayoristas colombianos basado en datos públicos, ciencia de datos y agentes de inteligencia artificial.

## Objetivo

VIGÍA busca detectar tempranamente cambios relevantes en mercados agrícolas mediante el análisis conjunto de:

- precios mayoristas;
- abastecimiento;
- procedencia;
- variables agroclimáticas;
- comportamiento histórico.

El sistema evolucionará hacia una arquitectura capaz de detectar anomalías, investigar evidencia, formular hipótesis, emitir alertas y auditar posteriormente su propio desempeño.

## Principios de ingeniería

El proyecto sigue cuatro principios fundamentales:

1. Python realiza los cálculos científicos.
2. Los modelos de lenguaje no sustituyen resultados cuantitativos.
3. Toda alerta debe ser trazable hasta sus datos y algoritmos de origen.
4. Ningún componente externo se considera confiable sin validación.

## Estado

### H0 — Fundación

Objetivos:

- entorno reproducible;
- Python 3.14;
- pruebas automatizadas;
- análisis estático;
- tipado estático;
- integración continua.

No forman parte todavía de H0:

- SIPSA;
- IDEAM;
- LangChain;
- LangGraph;
- Groq;
- Streamlit;
- modelos predictivos.

## Desarrollo

Instalar el proyecto:

```bash
python -m pip install -e ".[desarrollo]"
```

Ejecutar todas las validaciones:

```bash
ruff format --check .
ruff check .
mypy
pytest
```
## Estructura inicial

```bash
vigia-mercados/
├── .devcontainer/
├── .github/
│   └── workflows/
├── src/
│   └── vigia/
├── tests/
├── pyproject.toml
├── README.md
└── SECURITY.md
```
## Licencia

Pendiente de decisión.
