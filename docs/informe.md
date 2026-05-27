# Informe Lab 7 - RetailMax

Área de negocio elegida: **Ventas y Rentabilidad Comercial**.

La base RetailMax permite analizar el ciclo comercial completo: pedidos, detalle de venta, productos, categorías, clientes, tiendas, inventario, devoluciones y campañas. El dashboard se construye con 2 tabs y 12 indicadores, todos mediante **Native Query / SQL** en Metabase.

## Tab 1: Desempeño comercial

### 1. Ingresos netos totales

- **Nombre del indicador:** Ingresos netos totales.
- **Qué representa en términos de negocio:** Valor total vendido en pedidos completados, aplicando descuentos por línea.
- **Por qué es importante para el área:** Resume el tamaño del negocio y sirve como métrica principal para evaluar desempeño comercial.
- **Visualización usada y por qué:** Tarjeta KPI, porque es un único valor ejecutivo.
- **Consulta SQL completa usada en Metabase:**

```sql
SELECT
    ROUND(SUM(dp.cantidad * dp.precio_unitario * (1 - dp.descuento / 100.0)), 2) AS ingresos_netos
FROM pedido p
JOIN detalle_pedido dp ON dp.id_pedido = p.id_pedido
WHERE p.estado = 'completado';
```

### 2. Ingresos netos por mes

- **Nombre del indicador:** Ingresos netos por mes.
- **Qué representa en términos de negocio:** Evolución mensual de los ingresos netos.
- **Por qué es importante para el área:** Permite detectar crecimiento, caídas y estacionalidad.
- **Visualización usada y por qué:** Línea temporal, porque muestra tendencias en el tiempo.
- **Consulta SQL completa usada en Metabase:**

```sql
SELECT
    DATE_TRUNC('month', p.fecha)::date AS mes,
    ROUND(SUM(dp.cantidad * dp.precio_unitario * (1 - dp.descuento / 100.0)), 2) AS ingresos_netos
FROM pedido p
JOIN detalle_pedido dp ON dp.id_pedido = p.id_pedido
WHERE p.estado = 'completado'
GROUP BY mes
ORDER BY mes;
```

### 3. Ingresos por tienda

- **Nombre del indicador:** Ingresos por tienda.
- **Qué representa en términos de negocio:** Contribución de cada tienda a los ingresos netos.
- **Por qué es importante para el área:** Ayuda a comparar sucursales y priorizar acciones comerciales.
- **Visualización usada y por qué:** Gráfico de barras, porque facilita comparar tiendas.
- **Consulta SQL completa usada en Metabase:**

```sql
SELECT
    t.nombre AS tienda,
    ROUND(SUM(dp.cantidad * dp.precio_unitario * (1 - dp.descuento / 100.0)), 2) AS ingresos_netos
FROM pedido p
JOIN tienda t ON t.id_tienda = p.id_tienda
JOIN detalle_pedido dp ON dp.id_pedido = p.id_pedido
WHERE p.estado = 'completado'
GROUP BY t.nombre
ORDER BY ingresos_netos DESC;
```

### 4. Ingresos por categoría

- **Nombre del indicador:** Ingresos por categoría.
- **Qué representa en términos de negocio:** Ventas netas generadas por cada categoría de producto.
- **Por qué es importante para el área:** Identifica qué categorías sostienen el ingreso y cuáles requieren impulso.
- **Visualización usada y por qué:** Gráfico de barras, porque compara categorías de forma clara.
- **Consulta SQL completa usada en Metabase:**

```sql
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
```

### 5. Ticket promedio por canal

- **Nombre del indicador:** Ticket promedio por canal.
- **Qué representa en términos de negocio:** Monto promedio por pedido completado en tienda y online.
- **Por qué es importante para el área:** Permite comparar la calidad económica de cada canal.
- **Visualización usada y por qué:** Gráfico de barras, porque compara dos canales directamente.
- **Consulta SQL completa usada en Metabase:**

```sql
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
```

### 6. Top 10 productos por ingresos

- **Nombre del indicador:** Top 10 productos por ingresos.
- **Qué representa en términos de negocio:** Productos que más ingresos netos generan.
- **Por qué es importante para el área:** Ayuda a proteger inventario clave y priorizar promociones.
- **Visualización usada y por qué:** Tabla, porque muestra producto, unidades e ingresos con precisión.
- **Consulta SQL completa usada en Metabase:**

```sql
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
```

## Tab 2: Rentabilidad y cliente

### 7. Margen bruto por departamento

- **Nombre del indicador:** Margen bruto por departamento.
- **Qué representa en términos de negocio:** Ganancia bruta estimada por departamento, descontando costo unitario del producto.
- **Por qué es importante para el área:** Muestra qué líneas no solo venden más, sino cuáles dejan más margen.
- **Visualización usada y por qué:** Gráfico de barras, porque compara departamentos por rentabilidad.
- **Consulta SQL completa usada en Metabase:**

```sql
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
```

### 8. Tasa de devolución mensual

- **Nombre del indicador:** Tasa de devolución mensual.
- **Qué representa en términos de negocio:** Porcentaje del ingreso mensual comprometido por reembolsos.
- **Por qué es importante para el área:** Señala problemas de calidad, logística o satisfacción del cliente.
- **Visualización usada y por qué:** Línea temporal, porque muestra cambios mensuales del riesgo de devolución.
- **Consulta SQL completa usada en Metabase:**

```sql
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
```

### 9. Ingresos por segmento de cliente

- **Nombre del indicador:** Ingresos por segmento de cliente.
- **Qué representa en términos de negocio:** Distribución del ingreso entre clientes VIP, regulares y nuevos.
- **Por qué es importante para el área:** Ayuda a decidir estrategias de retención y adquisición.
- **Visualización usada y por qué:** Pie chart, porque muestra participación relativa por segmento.
- **Consulta SQL completa usada en Metabase:**

```sql
SELECT
    cl.segmento,
    ROUND(SUM(dp.cantidad * dp.precio_unitario * (1 - dp.descuento / 100.0)), 2) AS ingresos_netos
FROM pedido p
JOIN cliente cl ON cl.id_cliente = p.id_cliente
JOIN detalle_pedido dp ON dp.id_pedido = p.id_pedido
WHERE p.estado = 'completado'
GROUP BY cl.segmento
ORDER BY ingresos_netos DESC;
```

### 10. Frecuencia de compra por segmento

- **Nombre del indicador:** Frecuencia de compra por segmento.
- **Qué representa en términos de negocio:** Promedio de pedidos completados por cliente en cada segmento.
- **Por qué es importante para el área:** Mide recurrencia y ayuda a identificar segmentos más fieles.
- **Visualización usada y por qué:** Gráfico de barras, porque compara segmentos.
- **Consulta SQL completa usada en Metabase:**

```sql
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
```

### 11. Productos bajo stock mínimo por tienda

- **Nombre del indicador:** Productos bajo stock mínimo por tienda.
- **Qué representa en términos de negocio:** Cantidad de productos cuyo stock actual está por debajo del mínimo definido.
- **Por qué es importante para el área:** Reduce quiebres de stock y protege ventas futuras.
- **Visualización usada y por qué:** Gráfico de barras, porque prioriza tiendas con mayor riesgo operativo.
- **Consulta SQL completa usada en Metabase:**

```sql
SELECT
    t.nombre AS tienda,
    COUNT(*) AS productos_bajo_minimo
FROM inventario i
JOIN tienda t ON t.id_tienda = i.id_tienda
WHERE i.stock_actual < i.stock_minimo
GROUP BY t.nombre
ORDER BY productos_bajo_minimo DESC;
```

### 12. Eficiencia de campañas por tipo

- **Nombre del indicador:** Eficiencia de campañas por tipo.
- **Qué representa en términos de negocio:** Clientes impactados, respuestas, tasa de respuesta y costo por respuesta por tipo de campaña.
- **Por qué es importante para el área:** Permite comparar tácticas comerciales y reasignar presupuesto.
- **Visualización usada y por qué:** Tabla, porque combina varias métricas para cada tipo de campaña.
- **Consulta SQL completa usada en Metabase:**

```sql
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
```
