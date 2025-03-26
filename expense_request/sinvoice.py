from __future__ import unicode_literals
import frappe
from frappe import _
from frappe import utils

def validate(doc, method):
    """Validate Sales Invoice before submission, especially for POS transactions"""
    if doc.is_pos:
        # Ensure required fields are set for POS invoices
        if not doc.customer:
            frappe.throw(_("Customer is mandatory for POS invoices"))
        
        # Set Party Type to 'Customer' if not set
        if not doc.delivered_to:
            doc.delivered_to = 'Customer'
        
        # Set Party field to the Customer if not set
        if doc.customer and not doc.party:
            doc.party = doc.customer
        
        # Set sales_man from customer if available
        if doc.customer and not doc.sales_man:
            customer_sales_man = frappe.db.get_value("Customer", doc.customer, "cust_sales_man")
            if customer_sales_man:
                doc.sales_man = customer_sales_man
        
        # Set party_code from customer if available
        if doc.customer and not doc.party_code:
            client_code = frappe.db.get_value("Customer", doc.customer, "client_code")
            if client_code:
                doc.party_code = client_code