"""Product management endpoints"""
from fastapi import APIRouter, HTTPException, status
from typing import List

# TODO: Import your Pydantic models here
# from ..models.product_models import CreateProductRequest, ProductResponse

# TODO: Import your interactors/use cases here
# from test-router-project.domain.interactors.product import CreateProduct, GetProduct, ListProduct

router = APIRouter()

# TODO: Remove this in-memory storage and use proper repositories/interactors
product_db: dict[str, dict] = {}
product_counter = 0


@router.post(
    "",
    # response_model=ProductResponse,  # Uncomment when you have the model
    status_code=status.HTTP_201_CREATED,
    summary="Create a new product",
    description="Create a new product with the provided information"
)
async def create_product(
    # product_data: CreateProductRequest  # Uncomment when you have the model
):
    """Create a new product"""
    global product_counter
    product_counter += 1
    item_id = f"product_{product_counter}"

    # TODO: Replace with actual use case/interactor
    # Example: item = await CreateProduct(param=value)

    new_item = {
        "id": item_id,
        # Add your fields here
    }

    product_db[item_id] = new_item
    return new_item


@router.get(
    "",
    # response_model=List[ProductResponse],  # Uncomment when you have the model
    summary="List all products",
    description="Retrieve a list of all products"
)
async def list_products():
    """Get all products"""
    # TODO: Replace with actual use case/interactor
    # Example: items = await ListProducts()
    return list(product_db.values())


@router.get(
    "/{item_id}",
    # response_model=ProductResponse,  # Uncomment when you have the model
    summary="Get product by ID",
    description="Retrieve a specific product by its ID"
)
async def get_product(item_id: str):
    """Get a product by ID"""
    # TODO: Replace with actual use case/interactor
    # Example: item = await GetProduct(item_id=item_id)

    if item_id not in product_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product with id '{item_id}' not found"
        )

    return product_db[item_id]


@router.put(
    "/{item_id}",
    # response_model=ProductResponse,  # Uncomment when you have the model
    summary="Update product",
    description="Update an existing product"
)
async def update_product(
    item_id: str,
    # product_data: UpdateProductRequest  # Uncomment when you have the model
):
    """Update a product"""
    # TODO: Replace with actual use case/interactor
    # Example: item = await UpdateProduct(item_id=item_id, data=...)

    if item_id not in product_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product with id '{item_id}' not found"
        )

    # Update logic here
    return product_db[item_id]


@router.delete(
    "/{item_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete product",
    description="Delete a product by its ID"
)
async def delete_product(item_id: str):
    """Delete a product"""
    # TODO: Replace with actual use case/interactor
    # Example: await DeleteProduct(item_id=item_id)

    if item_id not in product_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product with id '{item_id}' not found"
        )

    del product_db[item_id]
