# Gestor de Finanzas Personales

Aplicación didáctica en Python, Flask, SQLite, HTML y plantillas Jinja. Usa únicamente Flask como dependencia externa; el acceso a SQLite y el hash de contraseñas usan la biblioteca estándar de Python.

## 1. Estructura lógica de la base de datos

```text
financial_models (1) ──< profiles >── (1) users (1) ──< questionnaires >── (1) financial_models
         │
         └── (1) ──< categories (1) ──< transactions >── (1) users
```

Relaciones y reglas principales:

- `users`: cuenta con correo único y hash de contraseña.
- `profiles`: datos visibles del usuario y método elegido; cada usuario tiene un perfil.
- `questionnaires`: respuestas de onboarding y modelo recomendado; cada usuario conserva un cuestionario.
- `financial_models`: catálogo de los cuatro métodos disponibles.
- `categories`: categorías de ingreso/gasto asociadas a un método. Una categoría no se comparte entre métodos.
- `transactions`: movimiento de un usuario, vinculado a una categoría y a un tipo; el monto se almacena como entero en centavos para evitar errores de redondeo.
- Las claves foráneas tienen activada la restricción de SQLite. La aplicación valida que la categoría seleccionada pertenezca al método actual del usuario.

## 2. Vistas y flujo de navegación

```text
Registro ──> Cuestionario ──> Recomendación ── aceptar ──> Panel
                                   │                         │
                                   └── rechazar ──> Elegir método
                                                             │
                                                             v
                         Panel <──> Registrar movimiento <──> Historial
                           │                                  │
                           └── cambiar método                 └── filtros de fecha/categoría
```

El panel presenta ingresos, gastos y balance del mes calendario actual, compara el gasto con el mes anterior y grafica los gastos del mes por categoría con SVG nativo. El historial admite filtros por fechas y categoría. Para mantener consistente el historial, el método queda bloqueado tras guardar el primer movimiento.

### Regla de recomendación

El cuestionario pregunta por estilo de planificación, estabilidad del ingreso y prioridad del ahorro. Cada respuesta suma puntos de manera transparente:

- Planificación detallada: +2 base cero.
- Preferencia por grupos/sobres: +2 sistema de sobres.
- Preferencia sencilla por porcentajes: +2 regla 50/30/20.
- Ingreso estable: +1 a 50/30/20 y +1 a base cero; ingreso variable: +1 a base cero y +1 a sobres.
- Ahorro prioritario: +2 págate primero; equilibrio: +1 a 50/30/20; aprender gastos: +1 a base cero y +1 a sobres.

Se recomienda el método con mayor puntuación; en empate se usa el orden 50/30/20, base cero, sobres y págate primero. La sugerencia nunca se aplica sin aceptación del usuario.

## 3. Backend, clases y rutas

La organización del código queda así:

```text
main.py
finanzas/
├── __init__.py          # fábrica de la aplicación Flask
├── config.py            # configuración
├── catalog.py           # modelos, categorías y preguntas iniciales
├── database.py          # SQLite y ciclo de vida de la conexión
├── models.py            # User y QuestionnaireRecommender
├── services.py          # reglas de acceso a modelos y categorías
├── decorators.py        # control de acceso a rutas
└── routes/
    ├── auth.py          # registro, login y logout
    ├── main.py          # página de entrada
    ├── onboarding.py    # cuestionario y elección de método
    └── transactions.py  # panel, movimientos e historial
```

- `finanzas/config.py`: configuración de rutas y clave de sesión.
- `finanzas/catalog.py`: modelos financieros, cuestionario y categorías iniciales.
- `finanzas/database.py`: conexión e inicialización del esquema SQLite.
- `finanzas/models.py`: clases `User` y `QuestionnaireRecommender`.
- `finanzas/services.py`: clase `FinanceService` para método y categorías del usuario.
- `finanzas/routes/`: rutas Flask separadas en autenticación, onboarding y movimientos.
- `finanzas/__init__.py`: fábrica `create_app()` que configura Flask y registra las rutas.
- `main.py`: punto de entrada pequeño para ejecutar la aplicación.

| Ruta | Función |
|---|---|
| `/register`, `/login`, `/logout` | Cuenta y sesión |
| `/onboarding` | Cuestionario de perfil |
| `/recommendation` | Aceptar sugerencia o continuar a elección manual |
| `/models` | Explicación y selección de los cuatro métodos |
| `/dashboard` | Resumen mensual y gráfica |
| `/transactions/new` | Registro de ingreso o gasto |
| `/history` | Historial y filtros |

## Ejecutar en Windows

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
$env:FLASK_SECRET_KEY = "reemplazar-por-una-clave-local-segura"
$env:FLASK_DEBUG = "1"
python main.py
```

Abre `http://127.0.0.1:5000`. La base `finanzas.db` se crea automáticamente al iniciar. Si no defines `FLASK_SECRET_KEY`, se genera una clave de sesión temporal nueva cada vez que arranca la aplicación; configura una clave fija y segura para conservar sesiones entre reinicios. `FLASK_DEBUG=1` solo debe usarse durante el desarrollo.
