import sqlite3
import os

DB_PATH = "data.db"

def seed_db():
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
        print(f"Removed existing {DB_PATH}")

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE Employee (
        EmployeeID INTEGER PRIMARY KEY AUTOINCREMENT,
        Name TEXT NOT NULL,
        Department TEXT NOT NULL,
        Salary INTEGER NOT NULL,
        HireDate DATE NOT NULL
    )
    """)

    employees = [
        ("Alice Smith", "Engineering", 120000, "2020-01-15"),
        ("Bob Johnson", "Engineering", 115000, "2021-03-22"),
        ("Charlie Brown", "Sales", 85000, "2019-11-01"),
        ("Diana Prince", "Management", 150000, "2018-05-10"),
        ("Evan Wright", "Marketing", 90000, "2022-08-14"),
        ("Fiona Gallagher", "Sales", 95000, "2020-07-19"),
        ("George Costanza", "Sales", 75000, "2023-01-05"),
        ("Hannah Abbott", "Engineering", 110000, "2021-09-09"),
        ("Ian Malcolm", "Research", 140000, "2017-02-14"),
        ("Julia Child", "Marketing", 92000, "2020-11-20"),
        ("Kevin Scott", "Engineering", 105000, "2022-04-11"),
        ("Laura Palmer", "HR", 80000, "2019-06-30"),
        ("Michael Scott", "Management", 130000, "2015-03-15"),
        ("Nina Dobrev", "Engineering", 125000, "2018-09-17"),
        ("Oscar Martinez", "Finance", 115000, "2016-08-08"),
        ("Pam Beesly", "Sales", 82000, "2019-02-14"),
        ("Quinn Fabray", "Marketing", 88000, "2021-12-01"),
        ("Rachel Green", "Sales", 89000, "2020-10-10"),
        ("Steve Rogers", "Management", 145000, "2017-07-04"),
        ("Tony Stark", "Engineering", 160000, "2015-05-02")
    ]

    cursor.executemany(
        "INSERT INTO Employee (Name, Department, Salary, HireDate) VALUES (?, ?, ?, ?)",
        employees
    )

    conn.commit()
    conn.close()
    print("Database seeded successfully with 20 employees.")

if __name__ == "__main__":
    seed_db()
