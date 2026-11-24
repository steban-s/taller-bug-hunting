Bug Hunting: API Taller Mecánico por Steban Solano

Este README documenta los 10 bugs encontrados y cómo se corrigieron.

La documentación interactiva queda en http://localhost:8000/docs.
<p align="center">
  <img src="https://media.tenor.com/YsjgzSRMrpwAAAAM/fish.gif" width="600">
</p>

1. GET /ordenes/ devolvía un dict en vez de una lista
Archivo: routers/ordenes.py
El response_model era List[OrdenResponse] pero se devolvía {"total": ..., "ordenes": ...}, lo que producía un error de validación.
-Antes
return {"total": len(ordenes), "ordenes": ordenes}
-Después
return resultado.scalars().all()

2. PATCH /ordenes/{id} pisaba campos con None
Archivo: routers/ordenes.py
model_dump() incluye los campos que el cliente no envió (como None), así que se borraban datos existentes.
-Antes
datos = orden_patch.model_dump()
-Después
datos = orden_patch.model_dump(exclude_unset=True)

3. DELETE /ordenes/{id} no borraba nada
Archivo: routers/ordenes.py
En AsyncSession, delete() es una corrutina y faltaba el await.
-Antes
db.delete(orden_db)
-Después
await db.delete(orden_db)

4. DELETE /mecanicos/{id} no guardaba el cambio
Archivo: routers/mecanicos.py
Se asignaba activo = False pero nunca se hacía commit.
-Antes
mecanico.activo = False
return None
-Después
mecanico.activo = False
await db.commit()
return None

5. OrdenResponse no podía leer objetos de SQLAlchemy
Archivo: schemas/schemas.py
le faltaba la configuración para validar desde atributos de objetos ORM.
model_config = {"from_attributes": True}

6. Referencia circular entre schemas
Archivo: schemas/schemas.py
MecanicoResponse contenía List[OrdenResponse] y OrdenResponse contenía MecanicoResponse, lo que genera recursión infinita. Se rompió el ciclo con schemas simples (MecanicoSimple y OrdenSimple) que no se anidan entre sí.

7. Lazy loading en async (MissingGreenlet)
Archivos: routers/ordenes.py y routers/mecanicos.py
Las relaciones mecanico y ordenes no se cargan solas en SQLAlchemy async, y al serializar la respuesta fallaba.
En los GET y en el PATCH: select(...).options(selectinload(...)).
En los POST: await db.refresh(obj, attribute_names=["relacion"]).

8. El modelo Repuesto no se importaba en main.py
Archivo: main.py
Sin el import, el modelo no se registra en Base.metadata y create_all nunca crea la tabla repuestos.
from models.repuesto import Repuesto

9. POST /ordenes/ no validaba el mecánico
Archivo: routers/ordenes.py
Se podían crear órdenes con un mecanico_id inexistente o de un mecánico desactivado (SQLite no valida llaves foráneas por defecto). Ahora ambos casos devuelven HTTP 400.
if not mecanico:
    raise HTTPException(status_code=400, detail="El mecánico no existe")
if not mecanico.activo:
    raise HTTPException(status_code=400, detail="El mecánico no está activo")

10. GET /mecanicos/ listaba mecánicos desactivados
Archivo: routers/mecanicos.py
El borrado es lógico, o sea que cuando se borra un mecánico no se elimina de verdad de la base de datos, solo se le pone activo = False para desactivarlo.
Pero el problema era que el listado de mecánicos traía a todos, sin fijarse si estaban activos o no. Entonces los mecánicos que ya estaban desactivados seguían apareciendo como si nada.
La corrección fue hacer que el GET solo traiga los mecánicos que tienen activo = True, así los desactivados quedan ocultos del listado pero siguen guardados en la base de datos con su activo = 0.