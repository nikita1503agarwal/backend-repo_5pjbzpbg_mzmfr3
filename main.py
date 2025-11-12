import os
from typing import List, Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from bson import ObjectId

from database import db, create_document, get_documents
from schemas import User, HouseCategory, Subcategory, Package, Quotation, QuotationItem

app = FastAPI(title="Interior Quotation System API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# -------- Helpers ---------
class IDModel(BaseModel):
    id: str


def to_object_id(id_str: str) -> ObjectId:
    try:
        return ObjectId(id_str)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid id")


def serialize(doc):
    if not doc:
        return doc
    doc["id"] = str(doc.pop("_id"))
    return doc


# -------- Root & Health ---------
@app.get("/")
def read_root():
    return {"message": "Interior Quotation System API running"}


@app.get("/test")
def test_database():
    response = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
        "database_url": None,
        "database_name": None,
        "connection_status": "Not Connected",
        "collections": []
    }
    try:
        if db is not None:
            response["database"] = "✅ Available"
            response["database_url"] = "✅ Set" if os.getenv("DATABASE_URL") else "❌ Not Set"
            response["database_name"] = "✅ Set" if os.getenv("DATABASE_NAME") else "❌ Not Set"
            try:
                response["collections"] = db.list_collection_names()
                response["database"] = "✅ Connected & Working"
                response["connection_status"] = "Connected"
            except Exception as e:
                response["database"] = f"⚠️  Connected but Error: {str(e)[:50]}"
        else:
            response["database"] = "⚠️  Available but not initialized"
    except Exception as e:
        response["database"] = f"❌ Error: {str(e)[:50]}"
    return response


# -------- CRUD: Users (admin/employee) --------
@app.post("/users", response_model=dict)
def create_user(payload: User):
    user_id = create_document("user", payload)
    return {"id": user_id}


@app.get("/users", response_model=List[dict])
def list_users(role: Optional[str] = None):
    filter_q = {"role": role} if role else {}
    docs = get_documents("user", filter_q)
    return [serialize(d) for d in docs]


# -------- CRUD: House Categories --------
@app.post("/house-categories", response_model=dict)
def create_house_category(payload: HouseCategory):
    new_id = create_document("housecategory", payload)
    return {"id": new_id}


@app.get("/house-categories", response_model=List[dict])
def list_house_categories():
    docs = get_documents("housecategory")
    return [serialize(d) for d in docs]


# -------- CRUD: Subcategories --------
@app.post("/subcategories", response_model=dict)
def create_subcategory(payload: Subcategory):
    # ensure house_category exists
    hc = db["housecategory"].find_one({"_id": to_object_id(payload.house_category_id)})
    if not hc:
        raise HTTPException(status_code=404, detail="House category not found")
    new_id = create_document("subcategory", payload)
    return {"id": new_id}


@app.get("/subcategories", response_model=List[dict])
def list_subcategories(house_category_id: Optional[str] = None):
    filter_q = {"house_category_id": house_category_id} if house_category_id else {}
    docs = get_documents("subcategory", filter_q)
    return [serialize(d) for d in docs]


# -------- CRUD: Packages --------
@app.post("/packages", response_model=dict)
def create_package(payload: Package):
    # ensure subcategory exists
    sc = db["subcategory"].find_one({"_id": to_object_id(payload.subcategory_id)})
    if not sc:
        raise HTTPException(status_code=404, detail="Subcategory not found")
    new_id = create_document("package", payload)
    return {"id": new_id}


@app.get("/packages", response_model=List[dict])
def list_packages(subcategory_id: Optional[str] = None):
    filter_q = {"subcategory_id": subcategory_id} if subcategory_id else {}
    docs = get_documents("package", filter_q)
    return [serialize(d) for d in docs]


# -------- CRUD: Quotations --------
@app.post("/quotations", response_model=dict)
def create_quotation(payload: Quotation):
    # ensure references exist
    emp = db["user"].find_one({"_id": to_object_id(payload.employee_id), "role": "employee"})
    if not emp:
        raise HTTPException(status_code=404, detail="Employee not found")
    hc = db["housecategory"].find_one({"_id": to_object_id(payload.house_category_id)})
    if not hc:
        raise HTTPException(status_code=404, detail="House category not found")
    sc = db["subcategory"].find_one({"_id": to_object_id(payload.subcategory_id)})
    if not sc:
        raise HTTPException(status_code=404, detail="Subcategory not found")

    # validate items' packages
    for item in payload.items:
        pkg = db["package"].find_one({"_id": to_object_id(item.package_id)})
        if not pkg:
            raise HTTPException(status_code=404, detail="Package not found in items")

    new_id = create_document("quotation", payload)
    return {"id": new_id}


@app.get("/quotations", response_model=List[dict])
def list_quotations(employee_id: Optional[str] = None):
    filter_q = {"employee_id": employee_id} if employee_id else {}
    docs = get_documents("quotation", filter_q)
    # calculate totals for convenience
    result = []
    for d in docs:
        items = d.get("items", [])
        subtotal = sum([(it.get("unit_price", 0) * it.get("quantity", 1)) for it in items])
        discount = (d.get("discount_percent", 0) / 100.0) * subtotal
        total = subtotal - discount
        d = serialize(d)
        d.update({"subtotal": subtotal, "discount_amount": discount, "total": total})
        result.append(d)
    return result


# Simple profile fetch by id
@app.get("/users/{user_id}", response_model=dict)
def get_user(user_id: str):
    doc = db["user"].find_one({"_id": to_object_id(user_id)})
    if not doc:
        raise HTTPException(status_code=404, detail="User not found")
    return serialize(doc)


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
