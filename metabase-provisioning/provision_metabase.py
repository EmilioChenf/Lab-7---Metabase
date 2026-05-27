import json
import os
import time
import urllib.error
import urllib.request


MB_URL = os.environ.get("MB_URL", "http://metabase:3000").rstrip("/")
EMAIL = os.environ["MB_ADMIN_EMAIL"]
PASSWORD = os.environ["MB_ADMIN_PASSWORD"]
FIRST_NAME = os.environ.get("MB_ADMIN_FIRST_NAME", "Calificador")
LAST_NAME = os.environ.get("MB_ADMIN_LAST_NAME", "UVG")
MARKER = "/metabase-data/.retailmax_dashboard_provisioned"


INDICATORS = [
    {
        "tab": "Desempeño comercial",
        "name": "Ingresos netos totales",
        "display": "scalar",
        "sql": """
SELECT
    ROUND(SUM(dp.cantidad * dp.precio_unitario * (1 - dp.descuento / 100.0)), 2) AS ingresos_netos
FROM pedido p
JOIN detalle_pedido dp ON dp.id_pedido = p.id_pedido
WHERE p.estado = 'completado';
""".strip(),
    },
    {
        "tab": "Desempeño comercial",
        "name": "Ingresos netos por mes",
        "display": "line",
        "sql": """
SELECT
    DATE_TRUNC('month', p.fecha)::date AS mes,
    ROUND(SUM(dp.cantidad * dp.precio_unitario * (1 - dp.descuento / 100.0)), 2) AS ingresos_netos
FROM pedido p
JOIN detalle_pedido dp ON dp.id_pedido = p.id_pedido
WHERE p.estado = 'completado'
GROUP BY mes
ORDER BY mes;
""".strip(),
    },
    {
        "tab": "Desempeño comercial",
        "name": "Ingresos por tienda",
        "display": "bar",
        "sql": """
SELECT
    t.nombre AS tienda,
    ROUND(SUM(dp.cantidad * dp.precio_unitario * (1 - dp.descuento / 100.0)), 2) AS ingresos_netos
FROM pedido p
JOIN tienda t ON t.id_tienda = p.id_tienda
JOIN detalle_pedido dp ON dp.id_pedido = p.id_pedido
WHERE p.estado = 'completado'
GROUP BY t.nombre
ORDER BY ingresos_netos DESC;
""".strip(),
    },
    {
        "tab": "Desempeño comercial",
        "name": "Ingresos por categoría",
        "display": "bar",
        "sql": """
SELECT
    c.nombre AS categoria,
    ROUND(SUM(dp.cantidad * dp.precio_unitario * (1 - dp.descuento / 100.0)), 2) AS ingresos_netos
FROM pedido p
JOIN detalle_pedido dp ON dp.id_pedido = p.id_pedido
JOIN producto pr ON pr.id_producto = dp.id_producto
JOIN categoria c ON c.id_categoria = pr.id_categoria
WHERE p.estado = 'completado'
GROUP BY c.nombre
ORDER BY ingresos_netos DESC;
""".strip(),
    },
    {
        "tab": "Desempeño comercial",
        "name": "Ticket promedio por canal",
        "display": "bar",
        "sql": """
WITH venta_pedido AS (
    SELECT
        p.id_pedido,
        p.canal,
        SUM(dp.cantidad * dp.precio_unitario * (1 - dp.descuento / 100.0)) AS total_pedido
    FROM pedido p
    JOIN detalle_pedido dp ON dp.id_pedido = p.id_pedido
    WHERE p.estado = 'completado'
    GROUP BY p.id_pedido, p.canal
)
SELECT
    canal,
    ROUND(AVG(total_pedido), 2) AS ticket_promedio
FROM venta_pedido
GROUP BY canal
ORDER BY ticket_promedio DESC;
""".strip(),
    },
    {
        "tab": "Desempeño comercial",
        "name": "Top 10 productos por ingresos",
        "display": "table",
        "sql": """
SELECT
    pr.nombre AS producto,
    SUM(dp.cantidad) AS unidades_vendidas,
    ROUND(SUM(dp.cantidad * dp.precio_unitario * (1 - dp.descuento / 100.0)), 2) AS ingresos_netos
FROM pedido p
JOIN detalle_pedido dp ON dp.id_pedido = p.id_pedido
JOIN producto pr ON pr.id_producto = dp.id_producto
WHERE p.estado = 'completado'
GROUP BY pr.nombre
ORDER BY ingresos_netos DESC
LIMIT 10;
""".strip(),
    },
    {
        "tab": "Rentabilidad y cliente",
        "name": "Margen bruto por departamento",
        "display": "bar",
        "sql": """
SELECT
    c.departamento,
    ROUND(SUM(dp.cantidad * ((dp.precio_unitario * (1 - dp.descuento / 100.0)) - pr.precio_costo)), 2) AS margen_bruto,
    ROUND(
        100.0 * SUM(dp.cantidad * ((dp.precio_unitario * (1 - dp.descuento / 100.0)) - pr.precio_costo))
        / NULLIF(SUM(dp.cantidad * dp.precio_unitario * (1 - dp.descuento / 100.0)), 0),
        2
    ) AS margen_porcentaje
FROM pedido p
JOIN detalle_pedido dp ON dp.id_pedido = p.id_pedido
JOIN producto pr ON pr.id_producto = dp.id_producto
JOIN categoria c ON c.id_categoria = pr.id_categoria
WHERE p.estado = 'completado'
GROUP BY c.departamento
ORDER BY margen_bruto DESC;
""".strip(),
    },
    {
        "tab": "Rentabilidad y cliente",
        "name": "Tasa de devolución mensual",
        "display": "line",
        "sql": """
WITH ventas AS (
    SELECT
        DATE_TRUNC('month', p.fecha)::date AS mes,
        SUM(dp.cantidad * dp.precio_unitario * (1 - dp.descuento / 100.0)) AS ingresos_netos
    FROM pedido p
    JOIN detalle_pedido dp ON dp.id_pedido = p.id_pedido
    WHERE p.estado IN ('completado', 'devuelto')
    GROUP BY mes
),
devoluciones AS (
    SELECT
        DATE_TRUNC('month', d.fecha)::date AS mes,
        SUM(d.monto_reembolso) AS monto_reembolsado
    FROM devolucion d
    GROUP BY mes
)
SELECT
    v.mes,
    ROUND(COALESCE(d.monto_reembolsado, 0), 2) AS monto_reembolsado,
    ROUND(100.0 * COALESCE(d.monto_reembolsado, 0) / NULLIF(v.ingresos_netos, 0), 2) AS tasa_devolucion_porcentaje
FROM ventas v
LEFT JOIN devoluciones d ON d.mes = v.mes
ORDER BY v.mes;
""".strip(),
    },
    {
        "tab": "Rentabilidad y cliente",
        "name": "Ingresos por segmento de cliente",
        "display": "pie",
        "sql": """
SELECT
    cl.segmento,
    ROUND(SUM(dp.cantidad * dp.precio_unitario * (1 - dp.descuento / 100.0)), 2) AS ingresos_netos
FROM pedido p
JOIN cliente cl ON cl.id_cliente = p.id_cliente
JOIN detalle_pedido dp ON dp.id_pedido = p.id_pedido
WHERE p.estado = 'completado'
GROUP BY cl.segmento
ORDER BY ingresos_netos DESC;
""".strip(),
    },
    {
        "tab": "Rentabilidad y cliente",
        "name": "Frecuencia de compra por segmento",
        "display": "bar",
        "sql": """
SELECT
    cl.segmento,
    COUNT(DISTINCT p.id_pedido) AS pedidos_completados,
    COUNT(DISTINCT cl.id_cliente) AS clientes,
    ROUND(COUNT(DISTINCT p.id_pedido)::numeric / NULLIF(COUNT(DISTINCT cl.id_cliente), 0), 2) AS pedidos_por_cliente
FROM cliente cl
JOIN pedido p ON p.id_cliente = cl.id_cliente
WHERE p.estado = 'completado'
GROUP BY cl.segmento
ORDER BY pedidos_por_cliente DESC;
""".strip(),
    },
    {
        "tab": "Rentabilidad y cliente",
        "name": "Productos bajo stock mínimo por tienda",
        "display": "bar",
        "sql": """
SELECT
    t.nombre AS tienda,
    COUNT(*) AS productos_bajo_minimo
FROM inventario i
JOIN tienda t ON t.id_tienda = i.id_tienda
WHERE i.stock_actual < i.stock_minimo
GROUP BY t.nombre
ORDER BY productos_bajo_minimo DESC;
""".strip(),
    },
    {
        "tab": "Rentabilidad y cliente",
        "name": "Eficiencia de campañas por tipo",
        "display": "table",
        "sql": """
SELECT
    ca.tipo,
    COUNT(*) AS clientes_impactados,
    SUM(CASE WHEN cc.respondio THEN 1 ELSE 0 END) AS respuestas,
    ROUND(100.0 * SUM(CASE WHEN cc.respondio THEN 1 ELSE 0 END) / NULLIF(COUNT(*), 0), 2) AS tasa_respuesta_porcentaje,
    ROUND(SUM(ca.presupuesto) / NULLIF(SUM(CASE WHEN cc.respondio THEN 1 ELSE 0 END), 0), 2) AS costo_por_respuesta
FROM campana ca
JOIN campana_cliente cc ON cc.id_campana = ca.id_campana
GROUP BY ca.tipo
ORDER BY tasa_respuesta_porcentaje DESC;
""".strip(),
    },
]


def request(method, path, token=None, payload=None, retries=1):
    data = None if payload is None else json.dumps(payload).encode("utf-8")
    headers = {"Content-Type": "application/json"}
    if token:
        headers["X-Metabase-Session"] = token
    req = urllib.request.Request(f"{MB_URL}{path}", data=data, headers=headers, method=method)
    for attempt in range(retries + 1):
        try:
            with urllib.request.urlopen(req, timeout=30) as response:
                raw = response.read().decode("utf-8")
                return json.loads(raw) if raw else {}
        except urllib.error.HTTPError as exc:
            body = exc.read().decode("utf-8", errors="replace")
            if attempt >= retries:
                raise RuntimeError(f"{method} {path} failed: {exc.code} {body}") from exc
            time.sleep(2)


def wait_for_metabase():
    for _ in range(300):
        try:
            request("GET", "/api/health")
            return
        except Exception:
            time.sleep(2)
    raise RuntimeError("Metabase no respondió a tiempo.")


def setup_or_login():
    props = request("GET", "/api/session/properties")
    token = props.get("setup-token")
    if token:
        payload = {
            "token": token,
            "user": {
                "email": EMAIL,
                "first_name": FIRST_NAME,
                "last_name": LAST_NAME,
                "password": PASSWORD,
            },
            "prefs": {
                "site_name": "RetailMax Lab 7",
                "site_locale": "es",
                "allow_tracking": False,
            },
            "database": {
                "engine": "postgres",
                "name": "RetailMax PostgreSQL",
                "details": {
                    "host": os.environ["POSTGRES_HOST"],
                    "port": int(os.environ["POSTGRES_PORT"]),
                    "dbname": os.environ["POSTGRES_DB"],
                    "user": os.environ["POSTGRES_USER"],
                    "password": os.environ["POSTGRES_PASSWORD"],
                    "ssl": False,
                    "ssl-mode": "disable",
                },
            },
        }
        try:
            result = request("POST", "/api/setup", payload=payload, retries=5)
            return result.get("id")
        except RuntimeError as exc:
            if "sólo puede utilizarse para crear el primer usuario" not in str(exc):
                raise

    result = request("POST", "/api/session", payload={"username": EMAIL, "password": PASSWORD}, retries=5)
    return result["id"]


def get_database_id(token):
    databases = request("GET", "/api/database", token=token)
    for db in databases.get("data", []):
        if db.get("name") == "RetailMax PostgreSQL":
            return db["id"]
    payload = {
        "engine": "postgres",
        "name": "RetailMax PostgreSQL",
        "details": {
            "host": os.environ["POSTGRES_HOST"],
            "port": int(os.environ["POSTGRES_PORT"]),
            "dbname": os.environ["POSTGRES_DB"],
            "user": os.environ["POSTGRES_USER"],
            "password": os.environ["POSTGRES_PASSWORD"],
            "ssl": False,
            "ssl-mode": "disable",
        },
        "is_full_sync": True,
    }
    # PostgreSQL may report healthy while docker-entrypoint-initdb.d is still loading DATA.sql.
    return request("POST", "/api/database", token=token, payload=payload, retries=30)["id"]


def create_dashboard(token):
    payload = {
        "name": "RetailMax - Lab 7 Visualización de Datos",
        "description": "Dashboard de ventas, rentabilidad y comportamiento del cliente creado con Native Query / SQL.",
    }
    return request("POST", "/api/dashboard", token=token, payload=payload)["id"]


def create_card(token, database_id, indicator):
    payload = {
        "name": indicator["name"],
        "description": f"{indicator['tab']} | Native Query SQL",
        "display": indicator["display"],
        "dataset_query": {
            "database": database_id,
            "type": "native",
            "native": {"query": indicator["sql"], "template-tags": {}},
        },
        "visualization_settings": {},
    }
    return request("POST", "/api/card", token=token, payload=payload)["id"]


def layout_dashboard(token, dashboard_id, card_ids):
    tab_names = ["Desempeño comercial", "Rentabilidad y cliente"]
    tab_ids = {name: -1 * (index + 1) for index, name in enumerate(tab_names)}
    per_tab_index = {name: 0 for name in tab_names}
    dashcards = []

    for indicator, card_id in zip(INDICATORS, card_ids):
        tab = indicator["tab"]
        index = per_tab_index[tab]
        per_tab_index[tab] = index + 1
        dashcards.append(
            {
                "id": -100 - len(dashcards),
                "card_id": card_id,
                "row": (index // 2) * 4,
                "col": (index % 2) * 12,
                "size_x": 12,
                "size_y": 4,
                "dashboard_tab_id": tab_ids[tab],
                "parameter_mappings": [],
                "visualization_settings": {},
                "series": [],
            }
        )

    payload = {
        "tabs": [{"id": tab_ids[name], "name": name} for name in tab_names],
        "cards": dashcards,
    }
    request("PUT", f"/api/dashboard/{dashboard_id}/cards", token=token, payload=payload)


def main():
    wait_for_metabase()

    if os.path.exists(MARKER):
        print("Metabase esta listo. Dashboard RetailMax ya fue aprovisionado; no se crean duplicados.")
        return

    token = setup_or_login()
    database_id = get_database_id(token)
    dashboard_id = create_dashboard(token)

    card_ids = []
    for indicator in INDICATORS:
        card_ids.append(create_card(token, database_id, indicator))
    layout_dashboard(token, dashboard_id, card_ids)

    with open(MARKER, "w", encoding="utf-8") as marker:
        marker.write(f"dashboard_id={dashboard_id}\n")
    print(f"Dashboard RetailMax creado en Metabase con id {dashboard_id}.")


if __name__ == "__main__":
    main()
