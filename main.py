"""API REST para administrar los libros de una biblioteca."""

import json
import logging
from pathlib import Path

from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, Field


app = FastAPI(title="API de la Biblioteca")
logger = logging.getLogger(__name__)
ARCHIVO_LIBROS = Path(__file__).resolve().parent / "datos" / "libros.json"


class LibroEntrada(BaseModel):
    """Datos que se reciben al crear o reemplazar un libro."""

    titulo: str = Field(min_length=3, max_length=100)
    autor: str = Field(min_length=3, max_length=60)
    anio: int = Field(ge=1000, le=2100)
    disponible: bool = True


class Libro(LibroEntrada):
    """Datos completos de un libro, incluido su identificador."""

    id: int


class LibroParcial(BaseModel):
    """Campos opcionales para modificar solamente lo indicado."""

    titulo: str | None = Field(default=None, min_length=3, max_length=100)
    autor: str | None = Field(default=None, min_length=3, max_length=60)
    anio: int | None = Field(default=None, ge=1000, le=2100)
    disponible: bool | None = None


def cargar_libros():
    """Lee el archivo JSON; si no existe o es inválido, comienza vacío."""
    try:
        with open(ARCHIVO_LIBROS, encoding="utf-8") as archivo:
            contenido = json.load(archivo)
        if not isinstance(contenido, list):
            return []
        return contenido
    except (FileNotFoundError, json.JSONDecodeError, UnicodeDecodeError):
        return []


def guardar_libros():
    """Guarda inmediatamente la lista de libros en el archivo JSON."""
    ARCHIVO_LIBROS.parent.mkdir(parents=True, exist_ok=True)
    with open(ARCHIVO_LIBROS, "w", encoding="utf-8") as archivo:
        json.dump(libros, archivo, ensure_ascii=False, indent=2)


def buscar_libro(id: int):
    """Encuentra un libro por su identificador o devuelve un error 404."""
    for libro in libros:
        if libro["id"] == id:
            return libro
    raise HTTPException(status_code=404, detail="Libro no encontrado")


# La lista se carga una sola vez al iniciar la aplicación.
libros = cargar_libros()
proximo_id = max((libro["id"] for libro in libros), default=0) + 1


@app.get("/", summary="Mensaje de bienvenida")
def inicio():
    """Devuelve el mensaje de bienvenida de la API."""
    return {"mensaje": "API de la biblioteca"}


@app.get("/libros", response_model=list[Libro], summary="Listar libros")
def listar_libros(
    autor: str | None = None,
    disponible: bool | None = None,
    desde: int = Query(default=0, ge=0),
    limite: int = Query(default=100, ge=0),
):
    """Filtra por autor y disponibilidad, y luego aplica paginación."""
    resultado = sorted(libros, key=lambda libro: libro["id"])
    if autor is not None:
        resultado = [
            libro for libro in resultado if libro["autor"].lower() == autor.lower()
        ]
    if disponible is not None:
        resultado = [
            libro for libro in resultado if libro["disponible"] == disponible
        ]
    return resultado[desde : desde + limite]


# Las rutas fijas deben estar antes de /libros/{id}.
@app.get("/libros/buscar", response_model=list[Libro], summary="Buscar libros")
def buscar_libros(texto: str):
    """Busca texto en el título o el autor, sin distinguir mayúsculas."""
    texto = texto.lower()
    return sorted(
        [
            libro
            for libro in libros
            if texto in libro["titulo"].lower() or texto in libro["autor"].lower()
        ],
        key=lambda libro: libro["id"],
    )


@app.get("/libros/estadisticas", summary="Estadísticas de libros")
def estadisticas():
    """Cuenta el total de libros, los disponibles y los prestados."""
    disponibles = sum(1 for libro in libros if libro["disponible"])
    return {
        "total": len(libros),
        "disponibles": disponibles,
        "prestados": len(libros) - disponibles,
    }


@app.post("/libros", response_model=Libro, status_code=201, summary="Crear libro")
def crear_libro(datos: LibroEntrada):
    """Crea un libro nuevo y evita títulos y autores duplicados."""
    global proximo_id
    for libro in libros:
        if (
            libro["titulo"].lower() == datos.titulo.lower()
            and libro["autor"].lower() == datos.autor.lower()
        ):
            raise HTTPException(status_code=409, detail="El libro ya existe")

    nuevo = {"id": proximo_id, **datos.model_dump()}
    libros.append(nuevo)
    proximo_id += 1
    guardar_libros()
    logger.info("Libro creado: %s", nuevo["id"])
    return nuevo


@app.get("/libros/{id}", response_model=Libro, summary="Consultar libro")
def obtener_libro(id: int):
    """Obtiene un libro por su identificador."""
    return buscar_libro(id)


@app.put("/libros/{id}", response_model=Libro, summary="Reemplazar libro")
def reemplazar_libro(id: int, datos: LibroEntrada):
    """Reemplaza todos los campos de un libro sin cambiar su id."""
    libro = buscar_libro(id)
    libro.update(datos.model_dump())
    guardar_libros()
    logger.info("Libro reemplazado: %s", id)
    return libro


@app.patch("/libros/{id}", response_model=Libro, summary="Actualizar libro")
def actualizar_libro(id: int, datos: LibroParcial):
    """Actualiza únicamente los campos enviados."""
    libro = buscar_libro(id)
    cambios = datos.model_dump(exclude_unset=True)
    # Los campos del libro no admiten null explícito.
    if any(valor is None for valor in cambios.values()):
        raise HTTPException(status_code=422, detail="Los campos no admiten null")
    libro.update(cambios)
    guardar_libros()
    logger.info("Libro actualizado: %s", id)
    return libro


@app.delete("/libros/{id}", status_code=204, summary="Eliminar libro")
def eliminar_libro(id: int):
    """Elimina un libro y responde sin contenido."""
    libro = buscar_libro(id)
    libros.remove(libro)
    guardar_libros()
    logger.info("Libro eliminado: %s", id)


@app.post("/libros/{id}/prestar", response_model=Libro, summary="Prestar libro")
def prestar_libro(id: int):
    """Marca un libro disponible como prestado."""
    libro = buscar_libro(id)
    if not libro["disponible"]:
        raise HTTPException(status_code=409, detail="El libro ya está prestado")
    libro["disponible"] = False
    guardar_libros()
    logger.info("Libro prestado: %s", id)
    return libro


@app.post("/libros/{id}/devolver", response_model=Libro, summary="Devolver libro")
def devolver_libro(id: int):
    """Marca un libro prestado como disponible."""
    libro = buscar_libro(id)
    if libro["disponible"]:
        raise HTTPException(status_code=409, detail="El libro ya está disponible")
    libro["disponible"] = True
    guardar_libros()
    logger.info("Libro devuelto: %s", id)
    return libro
