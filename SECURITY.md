# Seguridad

## Gestión de secretos

VIGÍA no almacena claves, tokens, credenciales ni secretos dentro del repositorio.

Los secretos necesarios para desarrollo o automatización deben administrarse mediante:

- GitHub Codespaces Secrets.
- GitHub Actions Secrets.
- Variables de entorno locales no versionadas.

Los archivos `.env` están excluidos del control de versiones.

## Datos externos

Toda información obtenida desde servicios externos se considera no confiable hasta haber sido:

1. descargada correctamente;
2. validada contra el esquema esperado;
3. normalizada;
4. verificada antes de ingresar al núcleo analítico.

## Dependencias

Las dependencias críticas deben declararse explícitamente y sus versiones deben mantenerse controladas.

No se aceptan actualizaciones automáticas de dependencias sin ejecución completa de:

- análisis estático;
- comprobación de tipos;
- pruebas automatizadas.

## Reporte de vulnerabilidades

Las vulnerabilidades no deben publicarse inicialmente como incidencias públicas.

Deben documentarse, reproducirse y corregirse antes de divulgar detalles que puedan facilitar explotación.
