import sqlalchemy
import logging
from src import database as db
from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel
from src.api import auth
from enum import Enum

router = APIRouter(
    prefix="/carts",
    tags=["cart"],
    dependencies=[Depends(auth.get_api_key)],
)

carts = {}
cart_items = {}

class search_sort_options(str, Enum):
    customer_name = "customer_name"
    item_sku = "item_sku"
    line_item_total = "line_item_total"
    timestamp = "timestamp"

class search_sort_order(str, Enum):
    asc = "asc"
    desc = "desc"   

@router.get("/search/", tags=["search"])
def search_orders(
    customer_name: str = "",
    potion_sku: str = "",
    search_page: str = "",
    sort_col: search_sort_options = search_sort_options.timestamp,
    sort_order: search_sort_order = search_sort_order.desc,
):
    """
    Search for cart line items by customer name and/or potion sku.

    Customer name and potion sku filter to orders that contain the 
    string (case insensitive). If the filters aren't provided, no
    filtering occurs on the respective search term.

    Search page is a cursor for pagination. The response to this
    search endpoint will return previous or next if there is a
    previous or next page of results available. The token passed
    in that search response can be passed in the next search request
    as search page to get that page of results.

    Sort col is which column to sort by and sort order is the direction
    of the search. They default to searching by timestamp of the order
    in descending order.

    The response itself contains a previous and next page token (if
    such pages exist) and the results as an array of line items. Each
    line item contains the line item id (must be unique), item sku, 
    customer name, line item total (in gold), and timestamp of the order.
    Your results must be paginated, the max results you can return at any
    time is 5 total line items.
    """

    return {
        "previous": "",
        "next": "",
        "results": [
            {
                "line_item_id": 1,
                "item_sku": "1 oblivion potion",
                "customer_name": "Scaramouche",
                "line_item_total": 50,
                "timestamp": "2021-01-01T00:00:00Z",
            }
        ],
    }


class Customer(BaseModel):
    customer_name: str
    character_class: str
    level: int

@router.post("/visits/{visit_id}")
def post_visits(visit_id: int, customers: list[Customer]):
    """
    Which customers visited the shop today?
    """
    print(customers)

    return "OK"


@router.post("/")
def create_cart(new_cart: Customer):
    """ """
    cart_id = len(carts) + 1
    carts[cart_id] = new_cart
    cart_items[cart_id] = {}
    return {"cart_id": cart_id}


class CartItem(BaseModel):
    quantity: int


@router.post("/{cart_id}/items/{item_sku}")
def set_item_quantity(cart_id: int, item_sku: str, cart_item: CartItem):
    """ """
    logging.debug(f"Cart Id: {cart_id}")
    logging.debug(f"Item SKU: {item_sku}")
    logging.debug(f"Cart Item: {cart_item}")

    if cart_id in carts:
        cart_items[cart_id][item_sku] = cart_item.quantity
        return "OK"
    else:
        return "Error"


class CartCheckout(BaseModel):
    payment: str

@router.post("/{cart_id}/checkout")
def checkout(cart_id: int, cart_checkout: CartCheckout):
    """ """
    logging.debug(f"Cart Id: {cart_id}")
    logging.debug(f"Cart Checkout: {cart_checkout}")

    if cart_id in carts:
        total_potions_bought = 0
        total_gold_paid = 0

        with db.engine.begin() as connection:
            result = connection.execute(sqlalchemy.text("SELECT num_green_potions FROM global_inventory;"))
            num_green_potions = result.mappings().one()['num_green_potions']

            for sku, quantity in cart_items[cart_id].items():
                if sku == "GREEN_POTION_0":
                    total_potions_bought += quantity
                    total_gold_paid += quantity * 50

            if total_potions_bought <= num_green_potions:
                sql_update_potions = sqlalchemy.text("""
                    UPDATE global_inventory
                    SET num_green_potions = num_green_potions - :total_potions_bought
                """)
                connection.execute(sql_update_potions, {'total_potions_bought': total_potions_bought})

                sql_update_gold = sqlalchemy.text("""
                    UPDATE global_inventory
                    SET gold = gold + :total_gold_paid
                """)
                connection.execute(sql_update_gold, {'total_gold_paid': total_gold_paid})

                logging.debug(f"Total Potions Bough: {total_potions_bought}")
                logging.debug(f"Total Gold Paid: {total_gold_paid}")

                return {
                    "total_potions_bought": total_potions_bought,
                    "total_gold_paid": total_gold_paid
                }
            else:
                return "Error"
    else:
        return "Error"
