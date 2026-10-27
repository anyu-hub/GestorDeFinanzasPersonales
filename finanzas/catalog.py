FINANCIAL_MODELS = (
    {
        "code": "503020",
        "name": "Regla 50/30/20",
        "description": "Distribuye el ingreso neto: 50% para necesidades, 30% para deseos y 20% para ahorro y pago de deudas.",
    },
    {
        "code": "zero_based",
        "name": "Presupuesto base cero",
        "description": "Asigna cada unidad de ingreso a una categoría planificada. Ingresos menos asignaciones deben resultar en cero.",
    },
    {
        "code": "envelopes",
        "name": "Sistema de sobres",
        "description": "Separa el dinero disponible en sobres por propósito y registra el gasto contra el sobre correspondiente.",
    },
    {
        "code": "pay_yourself",
        "name": "Págate a Ti Mismo Primero",
        "description": "Aparta una cantidad de ahorro al recibir ingresos y organiza el gasto con el dinero restante.",
    },
)

CATEGORIES_BY_MODEL = {
    "503020": [
        ("income", "Ingreso", "Sueldo"),
        ("income", "Ingreso", "Otro ingreso"),
        ("expense", "Necesidades (50%)", "Vivienda"),
        ("expense", "Necesidades (50%)", "Alimentación"),
        ("expense", "Necesidades (50%)", "Transporte"),
        ("expense", "Necesidades (50%)", "Salud"),
        ("expense", "Deseos (30%)", "Entretenimiento"),
        ("expense", "Deseos (30%)", "Restaurantes"),
        ("expense", "Deseos (30%)", "Compras personales"),
        ("expense", "Ahorro y deuda (20%)", "Ahorro"),
        ("expense", "Ahorro y deuda (20%)", "Pago de deudas"),
        ("expense", "Ahorro y deuda (20%)", "Otro"),
    ],
    "zero_based": [
        ("income", "Ingreso", "Sueldo"),
        ("income", "Ingreso", "Otro ingreso"),
        ("expense", "Asignaciones", "Vivienda"),
        ("expense", "Asignaciones", "Alimentación"),
        ("expense", "Asignaciones", "Transporte"),
        ("expense", "Asignaciones", "Servicios"),
        ("expense", "Asignaciones", "Salud"),
        ("expense", "Asignaciones", "Ahorro"),
        ("expense", "Asignaciones", "Deudas"),
        ("expense", "Asignaciones", "Otros"),
    ],
    "envelopes": [
        ("income", "Ingreso", "Sueldo"),
        ("income", "Ingreso", "Otro ingreso"),
        ("expense", "Sobre", "Vivienda"),
        ("expense", "Sobre", "Alimentación"),
        ("expense", "Sobre", "Transporte"),
        ("expense", "Sobre", "Servicios"),
        ("expense", "Sobre", "Salud"),
        ("expense", "Sobre", "Entretenimiento"),
        ("expense", "Sobre", "Ahorro"),
        ("expense", "Sobre", "Otros"),
    ],
    "pay_yourself": [
        ("income", "Ingreso", "Sueldo"),
        ("income", "Ingreso", "Otro ingreso"),
        ("expense", "Ahorro primero", "Ahorro prioritario"),
        ("expense", "Gastos esenciales", "Vivienda"),
        ("expense", "Gastos esenciales", "Alimentación"),
        ("expense", "Gastos esenciales", "Transporte"),
        ("expense", "Gastos esenciales", "Servicios y salud"),
        ("expense", "Gastos flexibles", "Entretenimiento"),
        ("expense", "Gastos flexibles", "Deudas y otros"),
    ],
}

QUESTION_OPTIONS = {
    "budgeting_style": {
        "detailed": "Me gusta planificar cada categoría con detalle",
        "flexible": "Prefiero separar dinero en grupos o sobres",
        "simple": "Prefiero una guía sencilla con porcentajes",
    },
    "income_stability": {
        "stable": "Mi ingreso suele ser estable",
        "variable": "Mi ingreso cambia de un mes a otro",
    },
    "savings_priority": {
        "high": "Quiero priorizar el ahorro desde que recibo dinero",
        "balanced": "Quiero equilibrar ahorro y gastos",
        "learning": "Primero quiero entender mejor mis gastos",
    },
}

MODEL_EXPLANATIONS = {
    "503020": "Es una guía simple para quien busca equilibrio sin planificar cada compra. Funciona mejor cuando el ingreso es relativamente predecible.",
    "zero_based": "Ayuda a quien quiere decidir de antemano el destino de todo su ingreso y revisar cada categoría con detalle.",
    "envelopes": "Es útil para controlar límites de gasto por propósito, especialmente si resulta más fácil pensar en grupos separados.",
    "pay_yourself": "Conviene a quien quiere convertir el ahorro en prioridad y apartarlo antes de organizar otros gastos.",
}
