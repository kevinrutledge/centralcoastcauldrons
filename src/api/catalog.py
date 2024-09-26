import sqlalchemy
from src import database as db
from fastapi import APIRouter

router = APIRouter()


@router.get("/catalog/", tags=["catalog"])
def get_catalog():
    """
    Each unique item combination must have only a single price.
    """
    with db.engine.begin() as connection:
        result = connection.execute(
            sqlalchemy.text("SELECT num_green_potions FROM global_inventory")
        )
        row = result.fetchone()
        if row:
            num_green_potions = row.num_green_potions
        else:
            num_green_potions = 0 

    if num_green_potions > 0:
        return [
            {
                "sku": "GREEN_POTION_0",
                "name": "Green Potion",
                "quantity": num_green_potions,
                "price": 50,
                "potion_type": [0, 100, 0, 0],
            }
        ]
    else:
        return []
