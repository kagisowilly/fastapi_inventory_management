from fastapi import FastAPI, HTTPException;
from tortoise.contrib.fastapi import register_tortoise
from models import (Supplier_pydantic, Supplier_pydanticIn, Supplier, product_pydanticIn, product_pydantic, Product)

# for emails
from typing import List

from fastapi import BackgroundTasks, FastAPI
from fastapi_mail import ConnectionConfig, FastMail, MessageSchema, MessageType
from pydantic import BaseModel, EmailStr
from starlette.responses import JSONResponse

# dotenv

from dotenv import dotenv_values

#credentials
credentials = dotenv_values(".env")

#Adding CORS headers
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

#Adding cors urls
#origins allowed to access the server

origins=[
    'http://localhost:3000'
]

#Add middleware
#What to allow 
app.add_middleware(
    CORSMiddleware,
    allow_origins = origins,
    allow_credentials = True,
    allow_methods = ["*"],
    allow_headers = ["*"]
)



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
    print(response)
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

@app.post('/product/{supplier_id}')
async def add_product(supplier_id: int, products_details: product_pydanticIn):
    supplier = await Supplier.get(id = supplier_id)
    products_details = products_details.dict(exclude_unset = True)
    products_details['revenue'] += products_details['quantity_sold'] * products_details['unit_price']
    product_obj  = await Product.create(**products_details, supplied_by = supplier)
    response = await product_pydantic.from_tortoise_orm(product_obj)
    return {"status": "ok", "data": response}




@app.get("/products")
async def all_products():
    response = await product_pydantic.from_queryset(Product.all())
    return {"status": "ok", "data": response}

@app.get("/product/{id}")
async def specific_product(id:int):
    response = await product_pydantic.from_queryset_single(Product.get(id = id))
    return {"status": "ok", "data": response}

@app.put("/product/{id}")
async def update_product(id: int, update_info: product_pydanticIn):
    product = await Product.get (id = id)
    update_info = update_info.dict(exclude_unset = True)
    product.name = update_info["name"]
    product.quantity_in_stock = update_info["quantity_in_stock"]
    product.revenue = (update_info["quantity_sold"] * update_info["unit_price"]) + update_info["revenue"]
    product.quantity_sold = update_info["quantity_sold"]
    product.unit_price = update_info["unit_price"]
    await Product.save()
    response = await product_pydantic.from_tortoise_orm(product)
    return {"status": "ok", "data": response}

@app.delete("/product/{id}")
async def delete_product(id: int):
    await Product.filter(id = id).delete()
    return {"status": "ok"}

class EmailSchema(BaseModel):
    email: List[EmailStr]

class EmailContent(BaseModel):
    message: str
    subject: str


conf = ConnectionConfig(
    MAIL_USERNAME =credentials["EMAIL"],
    MAIL_PASSWORD = credentials["PASS"],
    MAIL_FROM = credentials["EMAIL"],
    MAIL_PORT = 465,
    MAIL_SERVER = "smtp.gmail.com",
    MAIL_STARTTLS = False,
    MAIL_SSL_TLS = True,
    USE_CREDENTIALS = True,
    VALIDATE_CERTS = True
)

@app.post('/email/{product_id}')
async def send_email(product_id: int, content: EmailContent):
    product = await Product.get(id = product_id)
    supplier = await product.supplied_by
    supplier_email = [supplier.email]

    html = """
    <h4>Kagiso Business</h4>
    <br> 
    <p>{content.message}</p>
    <br>
    <h6>Best Regards</h6>
    <h6>Kagiso business</h6>

    """

    message = MessageSchema(
        subject=content.subject,
        recipients=supplier_email,
        body=html,
        subtype=MessageType.html)

    fm = FastMail(conf)
    await fm.send_message(message)
    return {'status': "ok"}


register_tortoise(
    app,
    db_url="sqlite://database.sqlite3",
    modules={"models": ["models"]},
    generate_schemas= True,
    add_exception_handlers=True
)