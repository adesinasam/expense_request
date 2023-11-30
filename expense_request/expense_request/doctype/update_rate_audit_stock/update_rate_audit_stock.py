# Copyright (c) 2023, Glistercp and contributors

import frappe
from frappe.model.document import Document


class UpdateRateAuditStock(Document):
    pass


@frappe.whitelist()
def update_standard_buying():
    items = frappe.get_all('Item Price', filters={'price_list': 'Standard Buying'}, fields=['item_code', 'price_list_rate'])

    for item in items:
        frappe.db.set_value('Item', item['item_code'], 'cost_price', item['price_list_rate'])

    frappe.db.commit()

    return "Standard Buying prices updated for all items."


@frappe.whitelist()
def update_standard_selling():
    items = frappe.get_all('Item Price', filters={'price_list': 'Standard Selling'}, fields=['item_code', 'price_list_rate'])

    for item in items:
        frappe.db.set_value('Item', item['item_code'], 'standard_rate', item['price_list_rate'])

    frappe.db.commit()

    return "Standard selling prices updated for all items."


@frappe.whitelist()
def update_outstation_selling():
    items = frappe.get_all('Item Price', filters={'price_list': 'Outstation Selling Prices'}, fields=['item_code', 'price_list_rate'])

    for item in items:
        frappe.db.set_value('Item', item['item_code'], 'outstation_selling_price', item['price_list_rate'])

    frappe.db.commit()

    return "Outstation Selling Prices prices updated for all items."
