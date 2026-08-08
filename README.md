# eTaxFlow

eTaxFlow is a Django-based MVP for internal invoice vaulting and invoicing workflows for BARREIRO CASANOVA CASTILLO TECHNOLOGIES, S.R.L.

## Features

- Organization and contact management
- Internal document code generation separated from official NCF/e-NCF values
- Document uploads with SHA-256 hashing and file metadata
- Invoice and invoice-line records with Decimal-based totals
- Placeholder e-CF/DGII artifact model and status tracking
- Audit event logging for uploads and status changes

## Setup

1. Create and activate a virtual environment
2. Install dependencies: `pip install -r requirements.txt`
3. Run migrations: `python manage.py migrate`
4. Create a superuser: `python manage.py createsuperuser`
5. Start the development server: `python manage.py runserver`

## Notes

- This MVP does not connect to DGII production services.
- Real certificate signing and XML schema validation are not implemented yet.
