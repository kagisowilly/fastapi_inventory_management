from fastapi import FastAPI, HTTPException;
from tortoise.contrib.fastapi import register_tortoise
from models import (Supplier_pydantic, Supplier_pydanticIn, Supplier)

app = FastAPI()

@app.get('/')
def index():
    return {"Go to /docs for documentation"}

@app.post("/supplier")
async def add_supplier(supplier_info: Supplier_pydanticIn):
    supplier_object = await Supplier.create(**supplier_info.dict(exclude_unset = True)) #Adds supplier to a database and returns a database responce object.
    response = await Supplier_pydantic.from_tortoise_orm(supplier_object)
    return {"status": "ok", "data": response}
    

@app.get("/supplier")
async def get_all_suppliers():
    response = await Supplier_pydantic.from_queryset(Supplier.all())
    return {"status": "ok", "data": response}

@app.get('/supplier/{supplier_id}')
async def get_specific_supplier(supplier_id):
    response = await Supplier_pydantic.from_queryset_single(Supplier.get(id = supplier_id))
    return {"status": "ok", "data": response}

@app.put('/supplier/{supplier_id}')
async def update_supplier(supplier_id: int, update_info: Supplier_pydanticIn):
    supplier = await Supplier.get(id=supplier_id)
    update_info = update_info.dict(exclude_unset= True)
    supplier.name = update_info['name']
    supplier.company = update_info["company"]
    supplier.phone = update_info["phone"]
    supplier.email = update_info["email"]
    await supplier.save()
    response = await Supplier_pydantic.from_tortoise_orm(supplier)
    return {"status": "ok", "data": response}

@app.delete('/supplier/{supplier_id}')
async def delete_supplier(supplier_id: int):
    try:
        supplier = await Supplier.get(id=supplier_id)
        if supplier:
            await supplier.delete()
            return {"status": "ok"}
        else:
            raise HTTPException(status_code=404, detail="Supplier not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

register_tortoise(
    app,
    db_url="sqlite://database.sqlite3",
    modules={"models": ["models"]},
    generate_schemas= True,
    add_exception_handlers=True
)