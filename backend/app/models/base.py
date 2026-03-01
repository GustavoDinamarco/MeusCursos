# app/models/base.py
"""
Classe base declarativa para todos os modelos SQLAlchemy.
Centraliza metadados e a convenção de nomenclatura de tabelas.
"""
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """
    Base declarativa SQLAlchemy 2.0.
    Todos os modelos herdam desta classe.
    """
    pass
