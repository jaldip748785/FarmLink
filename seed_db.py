import re
from app import create_app
from models import db

app = create_app()

with app.app_context():
    # Recreate tables to ensure clean state
    db.drop_all()
    db.create_all()
    print("Tables re-created successfully.")

    # Read and execute SQL inserts
    sql_files = [
        'database/districts.sql',
        'database/talukas.sql',
        'database/villages.sql',
        'database/catefgories.sql'
    ]

    for sql_file in sql_files:
        print(f"Executing seeding for: {sql_file}")
        with open(sql_file, 'r') as f:
            content = f.read()

            # Find the INSERT statements (case-insensitive, multi-line)
            insert_match = re.search(r'(INSERT\s+INTO\s+.*?;)', content, re.DOTALL | re.IGNORECASE)
            if insert_match:
                sql = insert_match.group(1)
                # Execute using SQLAlchemy session
                db.session.execute(db.text(sql))
                db.session.commit()
                print(f"Successfully seeded: {sql_file}")
            else:
                print(f"No INSERT statement found in: {sql_file}")

    print("Database seeding completed.")
