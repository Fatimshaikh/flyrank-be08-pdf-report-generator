from app.database import get_connection


def get_report_data():
    connection = get_connection()

    try:
        total_orders = connection.execute(
            """
            SELECT COUNT(*) AS total_orders
            FROM orders
            """
        ).fetchone()["total_orders"]

        total_revenue = connection.execute(
            """
            SELECT COALESCE(SUM(amount), 0) AS total_revenue
            FROM orders
            """
        ).fetchone()["total_revenue"]

        top_products = connection.execute(
            """
            SELECT
                product,
                COUNT(*) AS order_count,
                ROUND(SUM(amount), 2) AS revenue
            FROM orders
            GROUP BY product
            ORDER BY revenue DESC
            LIMIT 5
            """
        ).fetchall()

        orders_per_day = connection.execute(
            """
            SELECT
                created_at,
                COUNT(*) AS order_count
            FROM orders
            WHERE created_at >= DATE('now', '-6 days')
            GROUP BY created_at
            ORDER BY created_at
            """
        ).fetchall()

        return {
            "total_orders": total_orders,
            "total_revenue": round(total_revenue, 2),
            "top_products": [dict(row) for row in top_products],
            "orders_per_day": [dict(row) for row in orders_per_day],
        }

    finally:
        connection.close()