from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from backend.app.models.company import Company
from backend.app.db.session import SessionLocal
from backend.app.core.config import settings

def main():
    db = SessionLocal()
    
    try:
        existing = db.query(Company).filter(Company.ticker ==  settings.mvp_ticker).first()
        
        if existing:
            print(f"{settings.mvp_ticker} already exists with id={existing.id}")
            return 

        company = Company(
            ticker=settings.mvp_ticker,
            sector="Technology / Semiconductors",
            name=settings.mvp_company_name,
            exchange=settings.mvp_exchange
        )
        
        db.add(company)
        db.commit()
        db.refresh(company)
        
        print(f"Seeded {company.ticker} with id={company.id}")
        
    
    finally:
        db.close()

if __name__ == "__main__":
    main()
        