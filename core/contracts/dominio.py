"""Dominios de aplicación del sistema. Cada uno tiene su adaptador en adapters/<dominio>/."""

from enum import StrEnum


class Dominio(StrEnum):
    CIVIL = "civil"
    TELECOM = "telecom"
    INDUSTRIAL = "industrial"
    SISTEMAS = "sistemas"
