
import json
from datetime import date

from app.database import Base, DATA_DIR, SessionLocal, engine
from app.models import Patient, Report


SEED_FILE = DATA_DIR / "seed_data.json"


def seed_database() -> None:
    with SEED_FILE.open("r", encoding="utf-8") as file:
        seed_data = json.load(file)

    # Create tables if they do not exist.
    Base.metadata.create_all(bind=engine)

    with SessionLocal() as session:
        try:
            # This is a local synthetic database reset.
            session.query(Report).delete()
            session.query(Patient).delete()
            session.flush()

            patients = [
                Patient(
                    patient_id=item["patient_id"],
                    patient_name=item["patient_name"],
                    date_of_birth=date.fromisoformat(
                        item["date_of_birth"]
                    ),
                )
                for item in seed_data["patients"]
            ]

            session.add_all(patients)
            session.flush()

            reports = [
                Report(
                    report_id=item["report_id"],
                    patient_id=item["patient_id"],
                    report_type=item["report_type"],
                    report_date=date.fromisoformat(
                        item["report_date"]
                    ),
                    report_text=item["report_text"],
                    findings=item["findings"],
                    status=item["status"],
                )
                for item in seed_data["reports"]
            ]

            session.add_all(reports)
            session.commit()

            patient_count = session.query(Patient).count()
            report_count = session.query(Report).count()

            print("Database seeded successfully.")
            print(f"Patients: {patient_count}")
            print(f"Reports: {report_count}")

        except Exception:
            session.rollback()
            raise


if __name__ == "__main__":
    seed_database()
