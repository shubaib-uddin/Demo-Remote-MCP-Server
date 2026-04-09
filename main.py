from fastmcp import FastMCP
import os
import aiosqlite
import tempfile

TEMP_DIR = tempfile.gettempdir()
DB_PATH = os.path.join(TEMP_DIR, "expenses.db")
CATEGORIES_PATH = os.path.join(os.path.dirname(__file__), "categories.json")

print(f"Database path: {DB_PATH}")

mcp = FastMCP("ExpenseTracker")

def init_db():
    try:
        import sqlite3
        with sqlite3.connect(DB_PATH) as c:
            c.execute("PRAGMA journal_mode=WAL")
            c.execute("""
                CREATE TABLE IF NOT EXISTS expenses(
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date TEXT NOT NULL,
                    amount REAL NOT NULL,
                    category TEXT NOT NULL,
                    subcategory TEXT DEFAULT '',
                    note TEXT DEFAULT ''
                )
            """)
            c.execute("INSERT OR IGNORE INTO expenses(date, amount, category) VALUES ('2000-01-01', 0, 'test')")
            c.execute("DELETE FROM expenses WHERE category = 'test'")
            print("Database initialized successfully with write access")
    except Exception as e:
        print(f"Database initialization error: {e}")
        raise

init_db()

@mcp.tool()
async def add_expense(date, amount, category, subcategory="", note=""):
    '''Add a new expense entry to the database.'''
    try:
        async with aiosqlite.connect(DB_PATH) as c:
            cur = await c.execute(
                "INSERT INTO expenses(date, amount, category, subcategory, note) VALUES (?,?,?,?,?)",
                (date, amount, category, subcategory, note)
            )
            expense_id = cur.lastrowid
            await c.commit()
            return {"status": "success", "id": expense_id, "message": "Expense added successfully"}
    except Exception as e:
        if "readonly" in str(e).lower():
            return {"status": "error", "message": "Database is in read-only mode. Check file permissions."}
        return {"status": "error", "message": f"Database error: {str(e)}"}

@mcp.tool()
async def list_expenses(start_date, end_date):
    '''List expense entries within an inclusive date range.'''
    try:
        async with aiosqlite.connect(DB_PATH) as c:
            cur = await c.execute(
                """
                SELECT id, date, amount, category, subcategory, note
                FROM expenses
                WHERE date BETWEEN ? AND ?
                ORDER BY date DESC, id DESC
                """,
                (start_date, end_date)
            )
            cols = [d[0] for d in cur.description]
            return [dict(zip(cols, r)) for r in await cur.fetchall()]
    except Exception as e:
        return {"status": "error", "message": f"Error listing expenses: {str(e)}"}

@mcp.tool()
async def summarize(start_date, end_date, category=None):
    '''Summarize expenses by category within an inclusive date range.'''
    try:
        async with aiosqlite.connect(DB_PATH) as c:
            query = """
                SELECT category, SUM(amount) AS total_amount, COUNT(*) as count
                FROM expenses
                WHERE date BETWEEN ? AND ?
            """
            params = [start_date, end_date]

            if category:
                query += " AND category = ?"
                params.append(category)

            query += " GROUP BY category ORDER BY total_amount DESC"

            cur = await c.execute(query, params)
            cols = [d[0] for d in cur.description]
            return [dict(zip(cols, r)) for r in await cur.fetchall()]
    except Exception as e:
        return {"status": "error", "message": f"Error summarizing expenses: {str(e)}"}

# ✅ NEW: Update Expense Tool
@mcp.tool()
async def update_expense(id, date=None, amount=None, category=None, subcategory=None, note=None):
    '''Update an existing expense entry by its ID. Only provided fields will be updated.'''
    try:
        async with aiosqlite.connect(DB_PATH) as c:
            # Check if expense exists
            cur = await c.execute("SELECT id FROM expenses WHERE id = ?", (id,))
            row = await cur.fetchone()
            if not row:
                return {"status": "error", "message": f"No expense found with id {id}"}

            # Build dynamic SET clause for only provided fields
            fields = []
            params = []
            if date is not None:
                fields.append("date = ?")
                params.append(date)
            if amount is not None:
                fields.append("amount = ?")
                params.append(amount)
            if category is not None:
                fields.append("category = ?")
                params.append(category)
            if subcategory is not None:
                fields.append("subcategory = ?")
                params.append(subcategory)
            if note is not None:
                fields.append("note = ?")
                params.append(note)

            if not fields:
                return {"status": "error", "message": "No fields provided to update."}

            params.append(id)
            query = f"UPDATE expenses SET {', '.join(fields)} WHERE id = ?"
            await c.execute(query, params)
            await c.commit()
            return {"status": "success", "message": f"Expense with id {id} updated successfully"}
    except Exception as e:
        return {"status": "error", "message": f"Error updating expense: {str(e)}"}

# ✅ NEW: Delete Expense Tool
@mcp.tool()
async def delete_expense(id):
    '''Delete an expense entry by its ID.'''
    try:
        async with aiosqlite.connect(DB_PATH) as c:
            # Check if expense exists
            cur = await c.execute("SELECT id FROM expenses WHERE id = ?", (id,))
            row = await cur.fetchone()
            if not row:
                return {"status": "error", "message": f"No expense found with id {id}"}

            await c.execute("DELETE FROM expenses WHERE id = ?", (id,))
            await c.commit()
            return {"status": "success", "message": f"Expense with id {id} deleted successfully"}
    except Exception as e:
        return {"status": "error", "message": f"Error deleting expense: {str(e)}"}

@mcp.resource("expense:///categories", mime_type="application/json")
def categories():
    try:
        default_categories = {
            "categories": [
                "Food & Dining",
                "Transportation",
                "Shopping",
                "Entertainment",
                "Bills & Utilities",
                "Healthcare",
                "Travel",
                "Education",
                "Business",
                "Other"
            ]
        }
        try:
            with open(CATEGORIES_PATH, "r", encoding="utf-8") as f:
                return f.read()
        except FileNotFoundError:
            import json
            return json.dumps(default_categories, indent=2)
    except Exception as e:
        return f'{{"error": "Could not load categories: {str(e)}"}}'

if __name__ == "__main__":
    mcp.run(transport="http", host="0.0.0.0", port=8000)
from fastmcp import FastMCP
import os
import aiosqlite
import tempfile

TEMP_DIR = tempfile.gettempdir()
DB_PATH = os.path.join(TEMP_DIR, "expenses.db")
CATEGORIES_PATH = os.path.join(os.path.dirname(__file__), "categories.json")

print(f"Database path: {DB_PATH}")

mcp = FastMCP("ExpenseTracker")

def init_db():
    try:
        import sqlite3
        with sqlite3.connect(DB_PATH) as c:
            c.execute("PRAGMA journal_mode=WAL")
            c.execute("""
                CREATE TABLE IF NOT EXISTS expenses(
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date TEXT NOT NULL,
                    amount REAL NOT NULL,
                    category TEXT NOT NULL,
                    subcategory TEXT DEFAULT '',
                    note TEXT DEFAULT ''
                )
            """)
            c.execute("INSERT OR IGNORE INTO expenses(date, amount, category) VALUES ('2000-01-01', 0, 'test')")
            c.execute("DELETE FROM expenses WHERE category = 'test'")
            print("Database initialized successfully with write access")
    except Exception as e:
        print(f"Database initialization error: {e}")
        raise

init_db()

@mcp.tool()
async def add_expense(date, amount, category, subcategory="", note=""):
    '''Add a new expense entry to the database.'''
    try:
        async with aiosqlite.connect(DB_PATH) as c:
            cur = await c.execute(
                "INSERT INTO expenses(date, amount, category, subcategory, note) VALUES (?,?,?,?,?)",
                (date, amount, category, subcategory, note)
            )
            expense_id = cur.lastrowid
            await c.commit()
            return {"status": "success", "id": expense_id, "message": "Expense added successfully"}
    except Exception as e:
        if "readonly" in str(e).lower():
            return {"status": "error", "message": "Database is in read-only mode. Check file permissions."}
        return {"status": "error", "message": f"Database error: {str(e)}"}

@mcp.tool()
async def list_expenses(start_date, end_date):
    '''List expense entries within an inclusive date range.'''
    try:
        async with aiosqlite.connect(DB_PATH) as c:
            cur = await c.execute(
                """
                SELECT id, date, amount, category, subcategory, note
                FROM expenses
                WHERE date BETWEEN ? AND ?
                ORDER BY date DESC, id DESC
                """,
                (start_date, end_date)
            )
            cols = [d[0] for d in cur.description]
            return [dict(zip(cols, r)) for r in await cur.fetchall()]
    except Exception as e:
        return {"status": "error", "message": f"Error listing expenses: {str(e)}"}

@mcp.tool()
async def summarize(start_date, end_date, category=None):
    '''Summarize expenses by category within an inclusive date range.'''
    try:
        async with aiosqlite.connect(DB_PATH) as c:
            query = """
                SELECT category, SUM(amount) AS total_amount, COUNT(*) as count
                FROM expenses
                WHERE date BETWEEN ? AND ?
            """
            params = [start_date, end_date]

            if category:
                query += " AND category = ?"
                params.append(category)

            query += " GROUP BY category ORDER BY total_amount DESC"

            cur = await c.execute(query, params)
            cols = [d[0] for d in cur.description]
            return [dict(zip(cols, r)) for r in await cur.fetchall()]
    except Exception as e:
        return {"status": "error", "message": f"Error summarizing expenses: {str(e)}"}

# ✅ NEW: Update Expense Tool
@mcp.tool()
async def update_expense(id, date=None, amount=None, category=None, subcategory=None, note=None):
    '''Update an existing expense entry by its ID. Only provided fields will be updated.'''
    try:
        async with aiosqlite.connect(DB_PATH) as c:
            # Check if expense exists
            cur = await c.execute("SELECT id FROM expenses WHERE id = ?", (id,))
            row = await cur.fetchone()
            if not row:
                return {"status": "error", "message": f"No expense found with id {id}"}

            # Build dynamic SET clause for only provided fields
            fields = []
            params = []
            if date is not None:
                fields.append("date = ?")
                params.append(date)
            if amount is not None:
                fields.append("amount = ?")
                params.append(amount)
            if category is not None:
                fields.append("category = ?")
                params.append(category)
            if subcategory is not None:
                fields.append("subcategory = ?")
                params.append(subcategory)
            if note is not None:
                fields.append("note = ?")
                params.append(note)

            if not fields:
                return {"status": "error", "message": "No fields provided to update."}

            params.append(id)
            query = f"UPDATE expenses SET {', '.join(fields)} WHERE id = ?"
            await c.execute(query, params)
            await c.commit()
            return {"status": "success", "message": f"Expense with id {id} updated successfully"}
    except Exception as e:
        return {"status": "error", "message": f"Error updating expense: {str(e)}"}

# ✅ NEW: Delete Expense Tool
@mcp.tool()
async def delete_expense(id):
    '''Delete an expense entry by its ID.'''
    try:
        async with aiosqlite.connect(DB_PATH) as c:
            # Check if expense exists
            cur = await c.execute("SELECT id FROM expenses WHERE id = ?", (id,))
            row = await cur.fetchone()
            if not row:
                return {"status": "error", "message": f"No expense found with id {id}"}

            await c.execute("DELETE FROM expenses WHERE id = ?", (id,))
            await c.commit()
            return {"status": "success", "message": f"Expense with id {id} deleted successfully"}
    except Exception as e:
        return {"status": "error", "message": f"Error deleting expense: {str(e)}"}

@mcp.resource("expense:///categories", mime_type="application/json")
def categories():
    try:
        default_categories = {
            "categories": [
                "Food & Dining",
                "Transportation",
                "Shopping",
                "Entertainment",
                "Bills & Utilities",
                "Healthcare",
                "Travel",
                "Education",
                "Business",
                "Other"
            ]
        }
        try:
            with open(CATEGORIES_PATH, "r", encoding="utf-8") as f:
                return f.read()
        except FileNotFoundError:
            import json
            return json.dumps(default_categories, indent=2)
    except Exception as e:
        return f'{{"error": "Could not load categories: {str(e)}"}}'

if __name__ == "__main__":
    mcp.run(transport="http", host="0.0.0.0", port=8000)