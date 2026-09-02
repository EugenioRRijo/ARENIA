"""Extrae los dos presupuestos ARENAZA (Sesion M1.1 del PLAN_MULTIDOMINIO) a CSV canonicos
en `data/telecom/fuentes/`: `presupuesto_1_arenaza.csv` (14 renglones, 1109.29 USD) y
`presupuesto_2_arenaza.csv` (26 renglones, 5410.73 USD).

PyMuPDF no es dependencia del proyecto (mismo criterio que `scripts/extraer_maprex.py`, Sesion
M0.2: los PDF son evidencia de una sola sesion, no un flujo de la aplicacion). Ejecutar con:

    uv run --with pymupdf python scripts/extraer_arenaza.py

Que hace este script
--------------------
1. Lee el texto de `Presupuesto_1_ARENAZA.pdf` y `Presupuesto_2_ARENAZA.pdf`
   (`data/samples/telecom/`) con PyMuPDF. Cada PDF trae dos tablas: "Computos metricos"
   (pagina 1: item, unidad, cantidad) y "Presupuesto" (pagina 2: item, unidad, cantidad,
   precio unitario, total). Esta sesion transcribe la tabla "Presupuesto" (la que trae precio
   y total, que es lo que exige la cabecera del CSV) y usa "Computos metricos" solo para
   completar la descripcion cuando la columna de "Presupuesto" la trunca por ancho de columna
   fijo (ver `_FILAS_1`/`_FILAS_2`, mismo fenomeno que `_desc_material_o_equipo` en
   `extraer_maprex.py`) y para registrar la discrepancia del tubo corrugado.
2. Las 14 + 26 filas de `_FILAS_1`/`_FILAS_2` son una transcripcion curada, verificada a mano
   digito a digito contra el texto/tabla de cada PDF durante esta sesion (ver la bitacora
   `docs/bitacora/2026-09-02-M1.1-fuentes-arenaza.md`). `main()` no confia ciegamente en esa
   transcripcion: antes de escribir los CSV, `_verificar_contra_pdf()` comprueba que cada total
   de renglon y el total impreso del PDF (columna derecha de la tabla "Presupuesto", con coma de
   millar) aparecen efectivamente en el texto extraido por PyMuPDF de esa pagina. Si un total no
   aparece, `main()` se detiene con un error explicito en vez de escribir un CSV no verificado.
3. Escribe la cabecera exacta `renglon,descripcion,unidad,cantidad,precio_unitario,total,origen`
   (`origen` = `<pdf>:<pagina>:<renglon>`, pagina 1-indexada: 1 = Computos metricos, 2 =
   Presupuesto).

Convenciones y hallazgos declarados (para quien lea los CSV; ver tambien el README de la
carpeta y la bitacora de esta sesion)
-------------------------------------------------------------------------------------------
- `precio_unitario` vacio en la tabla "Presupuesto" de un renglon con `cantidad = 1` significa
  que el propio PDF omite el precio unitario por ser identico al total (columna redundante):
  este script SI completa ese vacio con `total / cantidad` (aqui, con el mismo valor que
  `total`, ya que dividir entre 1 no cambia el importe). Es una derivacion directa del mismo
  dato ya impreso, no un precio inventado.
- El renglon 14 de `presupuesto_1_arenaza.csv` ("Micelaneos") no tiene cantidad ni precio
  unitario en ninguna de las dos tablas del PDF: es una partida global de contingencia, sin
  base de cantidad x precio. Se deja `cantidad` y `precio_unitario` vacios (no se inventa una
  cantidad de "1" ni un precio "100.00" que el PDF no declara); `total` si esta en el PDF
  (100.00) y es el unico valor de esa fila que entra en la suma verificada por
  `tests/unit/test_fuentes_arenaza.py`.
- El renglon del "Tubo Corrugado Flexible 1 Pulgada" del presupuesto 2 (item 5) trae
  `cantidad = 90` en la tabla "Presupuesto" (unidad "Metros") pero `cantidad = 80` en la tabla
  "Computos metricos" de ESE MISMO PDF: es la inconsistencia de la fuente primaria que esta
  sesion registra tal cual (no se corrige), igual que las siete de la linea base civil. El CSV
  usa el valor de la tabla "Presupuesto" (90, la que trae precio y total); el fixture
  `tests/fixtures/presupuestos_arenaza.py` expone ambos valores en `TUBO_CORRUGADO`. Ademas, el
  precio unitario de ese renglon (99.75) esta cotizado POR TUBO DE 30 METROS, no por metro: el
  propio PDF anota el calculo como "3*99.75" (3 tubos x 30 m = 90 m); `total` = 299.25 es
  correcto para esa base de calculo, aunque `cantidad (90, en metros) x precio_unitario (99.75,
  por tubo)` no reproduce el total con una multiplicacion literal. Se preserva tal cual: no es
  el error que esta sesion debe registrar (ese es el 80/90), pero tampoco se oculta.
- Dos renglones del presupuesto 2 tienen un `total` impreso que no coincide con
  `cantidad x precio_unitario` (item 14, "Camara Bullet Ip 4mp Intemperie": 5 x 289.00 = 1445.00
  contra un total impreso de 1446.65; item 18, "Conector Jack Coupler Ubiquiti Rj45": 7 x 42.99 =
  300.93 contra un total impreso de 303.93). Se transcriben los tres valores tal como los
  imprime el PDF (no se recalcula `total` para que cuadre): son hallazgos adicionales del mismo
  tipo que las inconsistencias de la linea base civil, documentados en el README de la carpeta,
  fuera del alcance obligatorio de esta sesion (que solo debe registrar el 80/90 del tubo
  corrugado). No afectan el total del presupuesto: este script suma los `total` impresos, no
  los recalculados, y esa suma SI cierra exactamente en 5410.73 (verificado por
  `_verificar_contra_pdf` y por `tests/unit/test_fuentes_arenaza.py`).
- Varias descripciones de la tabla "Presupuesto" llegan truncadas por el ancho fijo de columna
  (por ejemplo "Switch Escritorio Gigabit De 10 Puertos" sin su sufijo "Con Poe De"): se
  completan con la version de la tabla "Computos metricos" del mismo PDF, que tiene una columna
  de Descripcion mas ancha. Cuando ninguna de las dos tablas trae el nombre completo sin
  truncar y el renglon ya fue verificado en `data/telecom/plantilla_precios.csv` (Sesion M0.1),
  se reutiliza esa transcripcion (misma fuente primaria, ya verificada a mano en esa sesion).
"""

from __future__ import annotations

import csv
import sys
from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path

try:
    import fitz  # PyMuPDF
except ImportError as exc:  # pragma: no cover - guia de uso, no logica de negocio
    raise SystemExit(
        "Falta PyMuPDF. Ejecutar con:\n"
        "  uv run --with pymupdf python scripts/extraer_arenaza.py"
    ) from exc

RAIZ = Path(__file__).resolve().parents[1]
CARPETA_PDF = RAIZ / "data" / "samples" / "telecom"
CARPETA_SALIDA = RAIZ / "data" / "telecom" / "fuentes"

RUTA_PDF_1 = CARPETA_PDF / "Presupuesto_1_ARENAZA.pdf"
RUTA_PDF_2 = CARPETA_PDF / "Presupuesto_2_ARENAZA.pdf"

CABECERA = ["renglon", "descripcion", "unidad", "cantidad", "precio_unitario", "total", "origen"]

PAGINA_PRESUPUESTO = 2  # 1-indexada: pagina 1 = Computos metricos, pagina 2 = Presupuesto


@dataclass(frozen=True, slots=True)
class FilaCurada:
    renglon: int
    descripcion: str
    unidad: str
    cantidad: str | None
    precio_unitario: str | None
    total: str


def _paginas_pdf(ruta: Path) -> list[str]:
    """El texto de cada pagina del PDF, por separado (no concatenado): la verificacion contra
    el PDF necesita distinguir la pagina 1 ("Computos metricos") de la pagina 2
    ("Presupuesto")."""
    with fitz.open(ruta) as doc:
        return [pagina.get_text() for pagina in doc]


# --------------------------------------------------------------------------------------
# Transcripcion curada de la tabla "Presupuesto" de cada PDF (pagina 2), verificada a mano
# digito a digito contra el render de la tabla durante esta sesion. Ver el docstring del
# modulo para las convenciones (precio_unitario derivado, Micelaneos sin cantidad/precio,
# descripciones completadas desde "Computos metricos").
# --------------------------------------------------------------------------------------

_FILAS_1: tuple[FilaCurada, ...] = (
    FilaCurada(1, "BOBINA CABLE UTP CAT 6 (300 M)", "Pieza", "1", "82.68", "82.68"),
    FilaCurada(
        2, "Switch Escritorio Gigabit De 10 Puertos Con Poe De", "Pieza", "1", "157.99", "157.99"
    ),
    FilaCurada(3, "Tubo Corrugado Flexible 1 Pulgada", "Metros", "90", "99.75", "299.25"),
    FilaCurada(4, "Conectores Rj45 Cat6 Utp Bolsa (100 unidades)", "Pieza", "1", "5.00", "5.00"),
    FilaCurada(5, "Bosla Tirrap (100 unidades)", "Pieza", "5", "2.00", "10.00"),
    FilaCurada(
        6, "Organizador De Cables Individuales 20cm 100 Und", "Pieza", "5", "18.00", "90.00"
    ),
    FilaCurada(7, "Bobina Cable Utp Cat6 305 m Int", "Pieza", "1", "211.21", "211.21"),
    FilaCurada(8, "Teipe Eléctrico Negro Cobra", "Pieza", "1", "9.99", "9.99"),
    FilaCurada(9, "Teipe Aislante Para Cableado Eléctrico", "Pieza", "1", "10.00", "10.00"),
    FilaCurada(
        10, "Toma Doble Con Tierra 270 20a Con Placa Blanca", "Pieza", "5", "5.05", "25.25"
    ),
    FilaCurada(11, "Anillo E.m.t. 2", "Pieza", "2", "3.96", "7.92"),
    FilaCurada(12, "Guaya Guia Pasa Cable De Acero", "Pieza", "1", "90.00", "90.00"),
    FilaCurada(
        13, "Cajetin Plástico 4x2 Pvc Con Grapa Metálica.", "Pieza", "5", "2.00", "10.00"
    ),
    FilaCurada(14, "Micelaneos", "", None, None, "100.00"),
)
TOTAL_PDF_1 = "1,109.29"

_FILAS_2: tuple[FilaCurada, ...] = (
    FilaCurada(1, "BOBINA CABLE UTP CAT 6 (300 M) Ext", "Pieza", "1", "96.99", "96.99"),
    FilaCurada(2, "Bobina Cable Utp Cat6 305 m Int", "Pieza", "1", "211.21", "211.21"),
    FilaCurada(3, "Punto De Acceso Rap Ruijie", "Pieza", "4", "208.92", "835.68"),
    FilaCurada(4, "Switch Tp-link Tl-sg108 8 Puertos", "Pieza", "1", "278.56", "278.56"),
    # Renglon del hallazgo 80/90: cantidad 90 aqui (tabla "Presupuesto"), 80 en "Computos
    # metricos" del mismo PDF. Precio unitario cotizado por tubo de 30 m (3*99.75=299.25).
    FilaCurada(5, "Tubo Corrugado Flexible 1 Pulgada 30 MTS", "Metros", "90", "99.75", "299.25"),
    FilaCurada(6, "Conectores Rj45 Cat6 Utp Bolsa (100 unidades)", "Pieza", "1", "5.00", "5.00"),
    FilaCurada(7, "Amarre Tiewrap Negro Plástico 20 Cm", "Pieza", "5", "2.84", "14.20"),
    FilaCurada(
        8, "Organizador De Cables Individuales 20cm 100 Und", "Pieza", "5", "19.00", "95.00"
    ),
    FilaCurada(9, "Protector De Voltaje Exceline", "Pieza", "4", "33.00", "132.00"),
    FilaCurada(10, "Rack Fijo Onlink 12u", "Pieza", "1", "202.00", "202.00"),
    FilaCurada(11, "Switch Tp-link 16 Puertos", "Pieza", "1", "160.00", "160.00"),
    FilaCurada(12, "Mini Ups Spidertec 17600mah", "Pieza", "1", "120.00", "120.00"),
    FilaCurada(13, "Nvr Hikvision 7600 Ds-7616ni-q2 16 Canales", "Pieza", "1", "118.75", "118.75"),
    # Total impreso (1446.65) no coincide con cantidad x precio_unitario (5*289.00=1445.00):
    # hallazgo adicional, no corregido (ver docstring del modulo y el README de la carpeta).
    FilaCurada(14, "Camara Bullet Ip 4mp Intemperie", "Pieza", "5", "289.00", "1446.65"),
    FilaCurada(15, "Cámara Domo Ip Hikvision 4mp", "Pieza", "5", "127.35", "636.75"),
    FilaCurada(16, "Cajetin Superficial 4x2 Hembra", "Pieza", "5", "50.00", "250.00"),
    FilaCurada(17, "Conector Rj-45 Ftp Cat6 Blindado 50 U", "Pieza", "2", "8.80", "17.60"),
    # Total impreso (303.93) no coincide con cantidad x precio_unitario (7*42.99=300.93):
    # segundo hallazgo adicional, mismo criterio de no corregir.
    FilaCurada(18, "Conector Jack Coupler Ubiquiti Rj45", "Pieza", "7", "42.99", "303.93"),
    FilaCurada(19, "Teipe Eléctrico Negro Cobra", "Pieza", "1", "9.99", "9.99"),
    FilaCurada(20, "Teipe Aislante Para Cableado Eléctrico", "Pieza", "1", "10.00", "10.00"),
    FilaCurada(21, "Canaleta Plastica 40x40x2mts", "Pieza", "2", "12.00", "24.00"),
    FilaCurada(22, "Base Para Tirrap Tirraje 10 u", "Pieza", "2", "5.00", "10.00"),
    FilaCurada(
        23, "Toma Doble Con Tierra 270 20a Con Placa Blanca", "Pieza", "5", "5.05", "25.25"
    ),
    FilaCurada(24, "Anillo E.m.t. 2", "Pieza", "2", "3.96", "7.92"),
    FilaCurada(
        25, "Cajetin Plástico 4x2 Pvc Con Grapa Metálica.", "Pieza", "5", "2.00", "10.00"
    ),
    FilaCurada(26, "Guaya Guia Pasa Cable De Acero", "Pieza", "1", "90.00", "90.00"),
)
TOTAL_PDF_2 = "5,410.73"

# Cantidad del tubo corrugado en la tabla "Computos metricos" (pagina 1) de cada PDF: PDF 1
# coincide con su propio presupuesto (90 y 90, sin inconsistencia); PDF 2 no (80 en computos
# metricos, 90 en presupuesto). Verificado a mano contra el render de ambas tablas.
CANTIDAD_COMPUTOS_TUBO_PDF_1 = "90"
CANTIDAD_COMPUTOS_TUBO_PDF_2 = "80"


def _verificar_contra_pdf(nombre_pdf: str, texto_paginas: list[str], filas, total_impreso) -> None:
    """Comprueba que cada total de renglon y el total impreso del PDF aparecen literalmente en
    el texto extraido de la pagina 2 ("Presupuesto"). No revalida cantidad/unidad/precio por
    renglon (el layout de dos columnas del PDF intercala esos valores con los de otras filas de
    forma no trivial de emparejar por texto plano); el total por renglon mas el total impreso
    ya bastan para detectar un renglon omitido, un total mal transcrito o un total del PDF que
    cambio, que es la verificacion critica para que la suma de la Meta 4 sea correcta.
    """
    texto_presupuesto = texto_paginas[PAGINA_PRESUPUESTO - 1]
    faltantes = [
        f"{nombre_pdf} renglon {fila.renglon} ({fila.descripcion}): total {fila.total} no "
        "aparece en el texto de la pagina 2 del PDF"
        for fila in filas
        if fila.total not in texto_presupuesto
    ]
    if total_impreso not in texto_presupuesto:
        faltantes.append(
            f"{nombre_pdf}: el total impreso {total_impreso} no aparece en el texto de la "
            "pagina 2 del PDF"
        )
    if faltantes:
        raise SystemExit(
            "Verificacion contra el PDF fallida (revisar _FILAS_1/_FILAS_2 o si el PDF "
            "cambio):\n  " + "\n  ".join(faltantes)
        )


def _precio_unitario(fila: FilaCurada) -> str:
    """`total / cantidad` cuando el PDF omite el precio unitario por ser igual al total
    (`cantidad = 1`); ya viene resuelto en `_FILAS_1`/`_FILAS_2`. Sin cantidad (Micelaneos) no
    hay precio unitario que derivar."""
    if fila.precio_unitario is None:
        return ""
    return fila.precio_unitario


def _fila_csv(nombre_pdf: str, fila: FilaCurada) -> dict[str, str]:
    return {
        "renglon": str(fila.renglon),
        "descripcion": fila.descripcion,
        "unidad": fila.unidad,
        "cantidad": fila.cantidad or "",
        "precio_unitario": _precio_unitario(fila),
        "total": fila.total,
        "origen": f"{nombre_pdf}:{PAGINA_PRESUPUESTO}:{fila.renglon}",
    }


def escribir_csv(ruta: Path, filas: list[dict[str, str]]) -> None:
    ruta.parent.mkdir(parents=True, exist_ok=True)
    with open(ruta, "w", newline="", encoding="utf-8") as f:
        escritor = csv.DictWriter(f, fieldnames=CABECERA)
        escritor.writeheader()
        escritor.writerows(filas)


def _suma(filas) -> Decimal:
    return sum((Decimal(fila.total) for fila in filas), Decimal("0"))


def main() -> int:
    paginas_1 = _paginas_pdf(RUTA_PDF_1)
    paginas_2 = _paginas_pdf(RUTA_PDF_2)

    _verificar_contra_pdf("Presupuesto_1_ARENAZA.pdf", paginas_1, _FILAS_1, TOTAL_PDF_1)
    _verificar_contra_pdf("Presupuesto_2_ARENAZA.pdf", paginas_2, _FILAS_2, TOTAL_PDF_2)

    total_1 = _suma(_FILAS_1)
    total_2 = _suma(_FILAS_2)
    if total_1 != Decimal("1109.29"):
        raise SystemExit(
            f"La suma de _FILAS_1 da {total_1}, se esperaba 1109.29. Revisar _FILAS_1 antes de "
            "escribir el CSV (no se debe forzar el total)."
        )
    if total_2 != Decimal("5410.73"):
        raise SystemExit(
            f"La suma de _FILAS_2 da {total_2}, se esperaba 5410.73. Revisar _FILAS_2 antes de "
            "escribir el CSV (no se debe forzar el total)."
        )

    filas_csv_1 = [_fila_csv("Presupuesto_1_ARENAZA.pdf", fila) for fila in _FILAS_1]
    filas_csv_2 = [_fila_csv("Presupuesto_2_ARENAZA.pdf", fila) for fila in _FILAS_2]

    escribir_csv(CARPETA_SALIDA / "presupuesto_1_arenaza.csv", filas_csv_1)
    escribir_csv(CARPETA_SALIDA / "presupuesto_2_arenaza.csv", filas_csv_2)

    print("Fuentes ARENAZA generadas:")
    print(f"  presupuesto_1_arenaza.csv -> {len(filas_csv_1)} renglones, total {total_1}")
    print(f"  presupuesto_2_arenaza.csv -> {len(filas_csv_2)} renglones, total {total_2}")
    print(
        "  tubo corrugado (presupuesto 2, renglon 5): 90 m en la tabla Presupuesto vs "
        f"{CANTIDAD_COMPUTOS_TUBO_PDF_2} m en Computos metricos (inconsistencia registrada, "
        "no corregida)"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
