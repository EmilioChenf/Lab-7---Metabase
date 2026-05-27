# RetailMax Metabase Lab 7

Proyecto reproducible para el **Lab 7: Visualización de Datos** usando PostgreSQL y Metabase con Docker Compose. El área elegida es **Ventas y Rentabilidad Comercial**, porque la base RetailMax incluye pedidos, detalle de pedidos, pagos, productos, clientes, inventario, devoluciones y campañas.

## Requisitos

- Docker Desktop o Docker Engine con Docker Compose.
- Puerto `3000` disponible para Metabase.
- Puerto `5432` disponible para PostgreSQL.

## Levantar el ambiente

```bash
docker compose up
```

El primer arranque hace lo siguiente:

1. Crea PostgreSQL con la base `retailmax`.
2. Ejecuta automáticamente `postgres-init/01_schema.sql` y `postgres-init/02_data.sql`.
3. Levanta Metabase en `http://localhost:3000`.
4. Crea el usuario de calificación.
5. Crea la conexión a PostgreSQL.
6. Crea el dashboard **RetailMax - Lab 7 Visualización de Datos** con 2 tabs y 12 indicadores SQL.
7. Guarda la configuración de Metabase en `metabase-data/`.

Si la consola muestra `retailmax_metabase_setup exited with code 0`, es normal: ese contenedor solo prepara Metabase y termina cuando el dashboard ya quedó creado.

## Acceso a Metabase

- URL: `http://localhost:3000`
- Correo: `calificar@uvg.edu.gt`
- Contraseña: `secret123+`

## Apagar el ambiente

```bash
docker compose down
```

Esto detiene los contenedores, pero conserva:

- El volumen Docker `postgres-data`.
- La carpeta local `metabase-data/` con el dashboard y la configuración de Metabase.

## Reiniciar desde cero

Usar esto solo si se quiere reconstruir la base y el dashboard desde cero:

```bash
docker compose down -v
```

Después eliminar el marcador local de aprovisionamiento si existe:

```bash
del metabase-data\.retailmax_dashboard_provisioned
```

Luego ejecutar nuevamente:

```bash
docker compose up
```

## Estructura

```text
retailmax-metabase-lab7/
├── postgres-init/
│   ├── 01_schema.sql
│   ├── 02_data.sql
│   └── 03_ready.sql
├── metabase-data/
│   └── metabase/
├── metabase-provisioning/
│   └── provision_metabase.py
├── docs/
│   ├── informe.md
│   └── informe.pdf
├── docker-compose.yml
├── .env
├── .gitignore
└── README.md
```

## Dashboard

El dashboard se organiza en 2 tabs:

- **Desempeño comercial**: ingresos, evolución mensual, tiendas, categorías, ticket promedio y productos top.
- **Rentabilidad y cliente**: margen, devoluciones, segmentos, frecuencia, inventario bajo mínimo y campañas.

Todos los indicadores se crean como **Native Query / SQL** desde `metabase-provisioning/provision_metabase.py`. La documentación completa de negocio y las consultas SQL están en `docs/informe.md` y `docs/informe.pdf`.

## Video de presentación

Duración máxima recomendada: 8 minutos.

Guion sugerido:

1. Introducción del área: explicar que el tablero analiza Ventas y Rentabilidad Comercial de RetailMax.
2. Recorrido del tab 1: mostrar desempeño comercial, crecimiento mensual, tiendas y productos.
3. Recorrido del tab 2: mostrar margen, devoluciones, clientes, inventario y campañas.
4. Top 3 indicadores: ingresos netos por mes, margen bruto por departamento y tasa de devolución mensual.
5. Indicador más importante: margen bruto por departamento, porque conecta ventas con costo y permite priorizar líneas rentables.

Enlace del video: **pendiente de pegar aquí**.

## Notas de evaluación

- No se usa MySQL.
- No hay archivos World Cup.
- PostgreSQL carga los scripts desde `docker-entrypoint-initdb.d`.
- Metabase persiste en `metabase-data/`.
- El usuario de calificación queda configurado automáticamente.
