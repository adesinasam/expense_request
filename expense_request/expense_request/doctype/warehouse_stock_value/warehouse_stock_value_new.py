# Copyright (c) 2023, Glistercp and contributors

import frappe
from frappe.model.document import Document
from frappe.utils import cint, cstr, flt

import erpnext
from erpnext.accounts.utils import get_company_default
from erpnext.controllers.stock_controller import StockController
from erpnext.stock.doctype.batch.batch import get_batch_qty
from erpnext.stock.doctype.serial_no.serial_no import get_serial_nos
from erpnext.stock.utils import get_stock_balance


class WarehouseStockValue(Document):
    pass


@frappe.whitelist()
def get_items(
    warehouse, posting_date, posting_time, company, ignore_empty_stock=True
):
    ignore_empty_stock = cint(ignore_empty_stock)
    items = get_items_for_stock_reco(warehouse, company)

    res = []

    for d in items:
            stock_bal = get_stock_balance(
                d.item_code,
                d.warehouse,
                posting_date,
                posting_time,
                with_valuation_rate=True,
                with_serial_no=cint(d.has_serial_no),
            )
            qty, valuation_rate, serial_no = (
                stock_bal[0],
                stock_bal[1],
                stock_bal[2] if cint(d.has_serial_no) else "",
            )

            if ignore_empty_stock and not stock_bal[0]:
                continue

            args = get_item_data(d, qty, valuation_rate, serial_no)

            res.append(args)

    # Create a new list to store the updated data
    updated_data = []

    # Loop through each item in the data
    for item in res:
        # Extract the item's information
        item_code = item['item_code']
        qty = item['qty']
        valuation_rate = item['valuation_rate']

        # Multiply qty and valuation_rate
        total_valuation = qty * valuation_rate

        # Create a new item dictionary with updated total_valuation
        updated_item = {
            'item_code': item_code,
            "warehouse": warehouse,
            'qty': qty,
            'valuation_rate': valuation_rate,
            'total_valuation': total_valuation
        }

        # Append the updated item to the new list
        updated_data.append(updated_item)


    total_stock_value = 0
    for row in updated_data:
        total_stock_value += row['total_valuation']

    # Check if the warehouse exists in the database
    if frappe.db.exists('Warehouse Stock Value', {'warehouse': warehouse}):
        # If the warehouse exists, update the total_stock_value
        existing_warehouse_stock_value = frappe.get_doc('Warehouse Stock Value', {'warehouse': warehouse})
        existing_warehouse_stock_value.total_stock_value = total_stock_value
        existing_warehouse_stock_value.save()
    else:
        # If the warehouse does not exist, create a new document and insert it
        warehouse_stock_value = frappe.new_doc('Warehouse Stock Value')
        warehouse_stock_value.warehouse = warehouse
        warehouse_stock_value.total_stock_value = total_stock_value
        warehouse_stock_value.insert()

    return total_stock_value


def get_items_for_stock_reco(warehouse, company):
    lft, rgt = frappe.db.get_value("Warehouse", warehouse, ["lft", "rgt"])
    items = frappe.db.sql(
        f"""
        select
            i.name as item_code, i.item_name, bin.warehouse as warehouse, i.has_serial_no, i.has_batch_no
        from
            tabBin bin, tabItem i
        where
            i.name = bin.item_code
            and IFNULL(i.disabled, 0) = 0
            and i.is_stock_item = 1
            and i.has_variants = 0
            and exists(
                select name from `tabWarehouse` where lft >= {lft} and rgt <= {rgt} and name = bin.warehouse
            )
    """,
        as_dict=1,
    )

    items += frappe.db.sql(
        """
        select
            i.name as item_code, i.item_name, id.default_warehouse as warehouse, i.has_serial_no, i.has_batch_no
        from
            tabItem i, `tabItem Default` id
        where
            i.name = id.parent
            and exists(
                select name from `tabWarehouse` where lft >= %s and rgt <= %s and name=id.default_warehouse
            )
            and i.is_stock_item = 1
            and i.has_variants = 0
            and IFNULL(i.disabled, 0) = 0
            and id.company = %s
        group by i.name
    """,
        (lft, rgt, company),
        as_dict=1,
    )

    # remove duplicates
    # check if item-warehouse key extracted from each entry exists in set iw_keys
    # and update iw_keys
    iw_keys = set()
    items = [
        item
        for item in items
        if [
            (item.item_code, item.warehouse) not in iw_keys,
            iw_keys.add((item.item_code, item.warehouse)),
        ][0]
    ]

    return items


def get_item_data(row, qty, valuation_rate, serial_no=None):
    return {
        "item_code": row.item_code,
        "warehouse": row.warehouse,
        "qty": qty,
        "valuation_rate": valuation_rate,
    }
