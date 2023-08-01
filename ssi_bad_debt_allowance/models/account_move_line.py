# Copyright 2023 OpenSynergy Indonesia
# Copyright 2023 PT. Simetri Sinergi Indonesia
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo import api, fields, models


class AccountMoveLine(models.Model):
    _name = "account.move.line"
    _inherit = ["account.move.line"]

    bad_debt_allowance_ids = fields.One2many(
        string="Bad Debt Allowance",
        comodel_name="bad_debt_allowance.detail",
        inverse_name="source_move_line_id",
    )
    amount_allowance = fields.Monetary(
        string="Amount Allowance",
        currency_field="company_currency_id",
        compute="_compute_amount_allowance",
        store=True,
    )

    @api.depends(
        "bad_debt_allowance_ids",
        "bad_debt_allowance_ids.amount_allowance",
        "bad_debt_allowance_ids.bad_debt_id.state",
    )
    def _compute_amount_allowance(self):
        for record in self:
            result = 0.0
            for allowance in record.bad_debt_allowance_ids:
                if allowance.bad_debt_id.state == "done":
                    result += allowance.amount_allowance
            record.amount_allowance = result
