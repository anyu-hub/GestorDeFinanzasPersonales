# Gestor de Finanzas Personales

Aplicación didáctica en Python, Flask, SQLite, HTML y plantillas Jinja. Usa únicamente Flask como dependencia externa; el acceso a SQLite y el hash de contraseñas usan la biblioteca estándar de Python.

## 1. Estructura lógica de la base de datos

```text
financial_models (1) ──< profiles >── (1) users (1) ──< questionnaires >── (1) financial_models
         │
         └── (1) ──< categories (1) ──< transactions >── (1) users
<<<<<<< HEAD
users (1) ──< monthly_budgets >── (1) categories
users (1) ── (1) cash_flow_settings
users (1) ──< savings_goals (1) ──< goal_contributions
=======
>>>>>>> 6ba1082df75101c13242f0ed5e05dbd2ef6db1e8
```

Relaciones y reglas principales:

- `users`: cuenta con correo único y hash de contraseña.
- `profiles`: datos visibles del usuario y método elegido; cada usuario tiene un perfil.
- `questionnaires`: respuestas de onboarding y modelo recomendado; cada usuario conserva un cuestionario.
- `financial_models`: catálogo de los cuatro métodos disponibles.
<<<<<<< HEAD
- `categories`: categorías predeterminadas de ingreso/gasto asociadas a un método, además de categorías personalizadas por usuario y método.
- `transactions`: movimiento de un usuario, vinculado a una categoría y a un tipo; los gastos registran si son fijos o variables y el monto se almacena como entero en centavos para evitar errores de redondeo.
- `monthly_budgets`: límite de gasto mensual de cada usuario por categoría.
- `cash_flow_settings`: ingreso recurrente mensual esperado que sirve como base para la proyección.
- `savings_goals` y `goal_contributions`: objetivos de ahorro y aportaciones registradas sin alterar los movimientos.
=======
- `categories`: categorías de ingreso/gasto asociadas a un método. Una categoría no se comparte entre métodos.
- `transactions`: movimiento de un usuario, vinculado a una categoría y a un tipo; el monto se almacena como entero en centavos para evitar errores de redondeo.
>>>>>>> 6ba1082df75101c13242f0ed5e05dbd2ef6db1e8
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

<<<<<<< HEAD
El panel presenta ingresos, gastos y balance del mes calendario actual, compara el gasto con el mes anterior y grafica los gastos del mes por categoría con SVG nativo. También estima el balance al cierre extrapolando el gasto observado y comparándolo con el ingreso recurrente mensual esperado que configura cada usuario; de ahí calcula una tasa de ahorro estimada. Los límites de presupuesto son manuales por categoría y el panel advierte al alcanzar el 80% o superar el límite. Cada gasto se clasifica como fijo o variable y el panel compara ambos importes del mes.

La sección de metas permite definir objetivos de ahorro y registrar aportaciones explícitas. Se conserva un historial contable separado de las transacciones; las aportaciones no crean ni modifican movimientos. El historial de movimientos admite filtros por fechas y categoría. Se pueden crear categorías propias desde el formulario de movimientos; quedan disponibles solo para su creador y el método activo. Para mantener consistente el historial, el método queda bloqueado tras guardar el primer movimiento.

### Regla de recomendación

Antes de responder el cuestionario, se muestran las explicaciones de los cuatro métodos financieros. El cuestionario pregunta por estilo de planificación, estabilidad del ingreso y prioridad del ahorro. Cada respuesta suma puntos de manera transparente:
=======
El panel presenta ingresos, gastos y balance del mes calendario actual, compara el gasto con el mes anterior y grafica los gastos del mes por categoría con SVG nativo. El historial admite filtros por fechas y categoría. Para mantener consistente el historial, el método queda bloqueado tras guardar el primer movimiento.

### Regla de recomendación

El cuestionario pregunta por estilo de planificación, estabilidad del ingreso y prioridad del ahorro. Cada respuesta suma puntos de manera transparente:
>>>>>>> 6ba1082df75101c13242f0ed5e05dbd2ef6db1e8

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
<<<<<<< HEAD
├── models.py            # usuarios, recomendador y proyección de flujo de caja
├── services.py          # servicios de método y planificación financiera
=======
├── models.py            # User y QuestionnaireRecommender
├── services.py          # reglas de acceso a modelos y categorías
>>>>>>> 6ba1082df75101c13242f0ed5e05dbd2ef6db1e8
├── decorators.py        # control de acceso a rutas
└── routes/
    ├── auth.py          # registro, login y logout
    ├── main.py          # página de entrada
    ├── onboarding.py    # cuestionario y elección de método
<<<<<<< HEAD
    ├── transactions.py  # panel, movimientos e historial
    └── planning.py      # presupuestos, flujo de caja y metas
=======
    └── transactions.py  # panel, movimientos e historial
>>>>>>> 6ba1082df75101c13242f0ed5e05dbd2ef6db1e8
```

- `finanzas/config.py`: configuración de rutas y clave de sesión.
- `finanzas/catalog.py`: modelos financieros, cuestionario y categorías iniciales.
- `finanzas/database.py`: conexión e inicialización del esquema SQLite.
<<<<<<< HEAD
- `finanzas/models.py`: clases `User`, `QuestionnaireRecommender` y cálculo de proyección de flujo de caja.
- `finanzas/services.py`: clases `FinanceService` y `PlanningService` para método y planificación financiera.
=======
- `finanzas/models.py`: clases `User` y `QuestionnaireRecommender`.
- `finanzas/services.py`: clase `FinanceService` para método y categorías del usuario.
>>>>>>> 6ba1082df75101c13242f0ed5e05dbd2ef6db1e8
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
<<<<<<< HEAD
| `/budgets` | Crear y administrar límites mensuales por categoría |
| `/cash-flow` | Guardar el ingreso mensual recurrente esperado |
| `/goals` | Crear metas de ahorro y registrar aportaciones |
=======
>>>>>>> 6ba1082df75101c13242f0ed5e05dbd2ef6db1e8

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
