from sqlalchemy.orm import declarative_base

Base = declarative_base()

# Export metadata for Alembic autogenerate
metadata = Base.metadata