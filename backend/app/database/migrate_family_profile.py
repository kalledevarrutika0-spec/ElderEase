from sqlalchemy import inspect, text

from app.database import engine


TABLE_COLUMNS = {
    "caregivers": (
        ("auth_user_id", "VARCHAR(255)"),
        ("family_id", "INTEGER"),
    ),
    "family_profiles": (),
    "family_members": (),
    "medicines": (("family_id", "INTEGER"),),
    "appointments": (("family_id", "INTEGER"),),
}


def migrate() -> None:
    inspector = inspect(engine)
    with engine.begin() as connection:
        for table_name, columns in TABLE_COLUMNS.items():
            if table_name not in inspector.get_table_names():
                continue
            existing = {column["name"] for column in inspector.get_columns(table_name)}
            for column_name, column_type in columns:
                if column_name not in existing:
                    connection.execute(
                        text(
                            f"ALTER TABLE {table_name} "
                            f"ADD COLUMN {column_name} {column_type}"
                        )
                    )
        inspector = inspect(engine)
        if "family_profiles" not in inspector.get_table_names():
            connection.execute(text(
                "CREATE TABLE family_profiles ("
                "id INTEGER PRIMARY KEY, family_name VARCHAR(120) NOT NULL, "
                "elder_name VARCHAR(120) NOT NULL, elder_age INTEGER, "
                "elder_care_notes TEXT, invite_code VARCHAR(32) NOT NULL UNIQUE, "
                "primary_caregiver_id INTEGER, "
                "created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP, "
                "updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP"
                ")"
            ))
        inspector = inspect(engine)
        if "family_members" not in inspector.get_table_names():
            connection.execute(text(
                "CREATE TABLE family_members ("
                "id INTEGER PRIMARY KEY, family_id INTEGER NOT NULL, "
                "caregiver_id INTEGER NOT NULL UNIQUE, "
                "auth_user_id VARCHAR(255) NOT NULL UNIQUE, "
                "role VARCHAR(80) NOT NULL, relationship VARCHAR(40) NOT NULL, "
                "is_primary BOOLEAN NOT NULL DEFAULT 0, "
                "created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP"
                ")"
            ))
        connection.execute(text(
            "INSERT INTO family_profiles "
            "(family_name, elder_name, elder_age, elder_care_notes, invite_code, primary_caregiver_id) "
            "SELECT 'Demo Care Family', 'Demo Care Recipient', 78, "
            "'Synthetic demo family profile.', 'DEMOFAMILY12', "
            "(SELECT id FROM caregivers ORDER BY id LIMIT 1) "
            "WHERE NOT EXISTS "
            "(SELECT 1 FROM family_profiles WHERE invite_code = 'DEMOFAMILY12')"
        ))
        demo_family_id = connection.execute(text(
            "SELECT id FROM family_profiles "
            "WHERE invite_code = 'DEMOFAMILY12' LIMIT 1"
        )).scalar_one()
        connection.execute(text(
            "UPDATE caregivers SET family_id = :family_id "
            "WHERE family_id IS NULL"
        ), {"family_id": demo_family_id})
        connection.execute(text(
            "UPDATE medicines SET family_id = COALESCE("
            "(SELECT family_id FROM caregivers "
            "WHERE caregivers.id = medicines.assigned_caregiver_id), "
            ":family_id) WHERE family_id IS NULL"
        ), {"family_id": demo_family_id})
        connection.execute(text(
            "UPDATE appointments SET family_id = COALESCE("
            "(SELECT family_id FROM caregivers "
            "WHERE caregivers.id = appointments.assigned_caregiver_id), "
            ":family_id) WHERE family_id IS NULL"
        ), {"family_id": demo_family_id})

    print("Family profile migration completed.")


if __name__ == "__main__":
    migrate()
