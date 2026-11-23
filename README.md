# API de la Biblioteca

Trabajo integrador del Bootcamp Python Backend de Silicon Misiones.
API REST desarrollada con FastAPI y Pydantic. Los libros se guardan en `datos/libros.json`, sin base de datos.

## Instalación (Windows, desde la carpeta del proyecto)

```powershell
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

## Ejecución

```powershell
uvicorn main:app --reload
```

Abrir `http://127.0.0.1:8000/docs` para probar los endpoints.

## Funcionalidades

- Crear, listar, consultar, reemplazar, actualizar y eliminar libros.
- Validación de datos con Pydantic y errores HTTP 404, 409 y 422.
- Filtros, paginación y búsqueda por título o autor.
- Persistencia en JSON, préstamos, devoluciones y estadísticas.

## Verificación

```powershell
python -c "import main"
ruff check .
```

Ruff es opcional y se instala aparte si se desea revisar el estilo del código.

## Notas

El archivo `datos/libros.json` se crea automáticamente al guardar el primer libro.
La API comienza con una lista vacía si el archivo no existe, está vacío o está dañado.
