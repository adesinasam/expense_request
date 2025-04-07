from __future__ import unicode_literals
import frappe
from frappe import _

def validate(doc, method):
    """Validate and auto-fill fields for Sales Invoice before saving"""
    if not doc.flags.before_save_processed:  # Prevent recursion
        doc.flags.before_save_processed = True

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
                if doc.cust_sales_man:
                    doc.sales_man = doc.cust_sales_man
        
            # Set party_code from customer if available
            if doc.customer and not doc.party_code:
                if doc.client_code:
                    doc.party_code = doc.client_code

        # Handle subsidiary company accounting dimension
        if not doc.get('custom_default_subsidiary_company'):
            return

        doc.subsidiary_company = doc.custom_default_subsidiary_company

        for item in doc.items:
            if item.subsidiary_company != doc.custom_default_subsidiary_company:
                item.subsidiary_company = doc.custom_default_subsidiary_company
