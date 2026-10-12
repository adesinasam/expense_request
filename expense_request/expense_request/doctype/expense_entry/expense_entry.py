# -*- coding: utf-8 -*-
# Copyright (c) 2020, Bantoo and contributors
# For license information, please see license.txt

# from __future__ import unicode_literals
# import frappe
# from frappe.model.document import Document

# class ExpenseEntry(Document):
	# pass

import frappe
from frappe.model.document import Document
from frappe.utils import flt
from erpnext.accounts.general_ledger import make_gl_entries
from erpnext.accounts.utils import get_account_currency
from erpnext.accounts.doctype.accounting_dimension.accounting_dimension import (
    get_accounting_dimensions,
)

class ExpenseEntry(Document):

    def on_submit(self):
        self.make_gl_entries()

    def on_cancel(self):
        # Un-match this entry from any Mint / Bank Transaction it was reconciled with
        from erpnext.accounts.doctype.bank_transaction.bank_transaction import (
            remove_from_bank_transaction,
        )
        remove_from_bank_transaction(self.doctype, self.name)
        self.db_set("clearance_date", None)

        frappe.db.sql(
            """
            DELETE FROM `tabGL Entry`
            WHERE voucher_type=%s AND voucher_no=%s
            """,
            (self.doctype, self.name),
        )

    @frappe.whitelist()
    def get_gl_preview(self):
        return self.build_gl_entries(preview=True)

    def make_gl_entries(self):
        gl_entries = self.build_gl_entries(preview=False)
        make_gl_entries(gl_entries, cancel=False, adv_adj=False)

    def build_gl_entries(self, preview=False):
        gl_entries = []
        # total_tax = 0
        expense_accounts = []

        pay_account = None
        if (self.mode_of_payment != "Cash" and (not 
        	self.payment_reference or not self.reference_date)):
        	frappe.throw(
        		title="Enter Payment Reference",
        		msg="Payment Reference and Date are Required for all non-cash payments."
        	)

        pay_account = frappe.db.get_value('Mode of Payment Account', {'parent' : self.mode_of_payment, 'company' : self.company}, 'default_account')

        if not pay_account or pay_account == "":
        	frappe.throw(
        		title="Error",
        		msg="The selected Mode of Payment has no linked account."
        	)
        

        for row in self.expenses:
            expense_accounts.append(row.expense_account)

            gl_entries.append(
                self.get_gl_dict(
                    account=row.expense_account,
                    debit=row.amount,
                    credit=0,
                    against_account=pay_account,
                    remarks=row.description or self.remarks or "Expense",
                    cost_center=row.cost_center or self.default_cost_center,
                    project=row.project or self.default_project or "",
                )
            )

            # total_tax += flt(row.tax_amount)


        # if total_tax > 0 and self.tax_account:
        #     expense_accounts.append(self.tax_account)

        #     gl_entries.append(
        #         self.get_gl_dict(
        #             account=self.tax_account,
        #             debit=total_tax,
        #             credit=0,
        #             against_account=self.payable_account,
        #             remarks="Tax",
        #         )
        #     )


        gl_entries.append(
            self.get_gl_dict(
                account=pay_account,
                debit=0,
                credit=self.total,
                against_account=", ".join(expense_accounts),
                remarks=self.remarks or "Expense Settlement",
                cost_center=self.default_cost_center or "",
                project=self.default_project or "",
            )
        )


        return gl_entries

    def get_gl_dict(
        self,
        account,
        debit=0,
        credit=0,
        against_account=None,
        remarks=None,
        cost_center=None,
        project=None,
    ):
        """
        Correct GL Entry for ERPNext v15
        """

        account_type, is_group = frappe.db.get_value(
            "Account", account, ["account_type", "is_group"]
        )

        if is_group:
            frappe.throw(f"Account {account} is a Group Account")

        account_currency = get_account_currency(account)

        # party_type = None
        # party = None

        # if account_type in ("Payable", "Receivable"):
        #     party_type = self.claimant_type
        #     party = self.party

        debit = flt(debit)
        credit = flt(credit)

        # return frappe._dict({
        #     "posting_date": self.posting_date,
        #     "company": self.company,
        #     "voucher_type": self.doctype,
        #     "voucher_subtype": self.doctype,
        #     "voucher_no": self.name,
        #     "account": account,

        #     "debit": debit,
        #     "credit": credit,

        #     "account_currency": account_currency,
        #     "debit_in_account_currency": debit,
        #     "credit_in_account_currency": credit,

        #     # "party_type": party_type,
        #     # "party": party,

        #     "against": against_account,
        #     "against_account": against_account,

        #     "cost_center": cost_center,
        #     "project": project,
        #     "remarks": remarks,
        #     "is_opening": "No",
        # })

        gl = frappe._dict({
            "posting_date": self.posting_date,
            "company": self.company,
            "voucher_type": self.doctype,
            "voucher_subtype": self.doctype,
            "voucher_no": self.name,

            "account": account,

            "debit": debit,
            "credit": credit,

            "account_currency": account_currency,
            "debit_in_account_currency": debit,
            "credit_in_account_currency": credit,

            "against": against_account,
            "against_account": against_account,

            "cost_center": cost_center,
            "project": project,

            "remarks": remarks,
            "is_opening": "No",
        })

        # Copy every Accounting Dimension from the parent document
        for dimension in get_accounting_dimensions():
            if self.meta.has_field(dimension):
                gl[dimension] = self.get(dimension)

        return gl