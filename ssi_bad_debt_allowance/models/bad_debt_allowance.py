# Copyright 2023 OpenSynergy Indonesia
# Copyright 2023 PT. Simetri Sinergi Indonesia
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models
from odoo.exceptions import UserError

from odoo.addons.ssi_decorator import ssi_decorator


class BadDebtAllowance(models.Model):
    _name = "bad_debt_allowance"
    _description = "Bad Debt Allowance"
    _inherit = [
        "mixin.transaction_confirm",
        "mixin.transaction_done",
        "mixin.transaction_cancel",
        "mixin.company_currency",
    ]

    # Multiple Approval Attribute
    _approval_from_state = "draft"
    _approval_to_state = "done"
    _approval_state = "confirm"
    _after_approved_method = "action_done"

    # Attributes related to add element on view automatically
    _automatically_insert_view_element = True
    _automatically_insert_multiple_approval_page = True
    _automatically_insert_done_button = False
    _automatically_insert_done_policy_fields = False

    _statusbar_visible_label = "draft,confirm,done"

    _policy_field_order = [
        "confirm_ok",
        "approve_ok",
        "reject_ok",
        "restart_approval_ok",
        "cancel_ok",
        "restart_ok",
        "done_ok",
        "manual_number_ok",
    ]

    _header_button_order = [
        "action_confirm",
        "action_approve_approval",
        "action_reject_approval",
        "action_done",
        "%(ssi_transaction_cancel_mixin.base_select_cancel_reason_action)d",
        "action_restart",
    ]

    # Attributes related to add element on search view automatically
    _state_filter_order = [
        "dom_draft",
        "dom_confirm",
        "dom_reject",
        "dom_done",
        "dom_cancel",
    ]

    # Sequence attribute
    _create_sequence_state = "done"

    date = fields.Date(
        string="Date",
        required=True,
    )
    type_id = fields.Many2one(
        string="Type",
        comodel_name="bad_debt_allowance_type",
        required=True,
        ondelete="restrict",
    )
    partner_id = fields.Many2one(
        string="Partner",
        comodel_name="res.partner",
        required=True,
        ondelete="restrict",
    )
    journal_id = fields.Many2one(
        string="Journal",
        comodel_name="account.journal",
        required=True,
        ondelete="restrict",
    )
    allowance_account_id = fields.Many2one(
        string="Allowance Account",
        comodel_name="account.account",
        required=True,
        ondelete="restrict",
    )
    expense_account_id = fields.Many2one(
        string="Expense Account",
        comodel_name="account.account",
        required=True,
        ondelete="restrict",
    )
    move_id = fields.Many2one(
        string="# Move",
        comodel_name="account.move",
        readonly=True,
    )
    detail_ids = fields.One2many(
        string="Details",
        comodel_name="bad_debt_allowance.detail",
        inverse_name="bad_debt_id",
    )
    state = fields.Selection(
        string="State",
        default="draft",
        selection=[
            ("draft", "Draft"),
            ("confirm", "Waiting for Approval"),
            ("done", "Done"),
            ("cancel", "Cancelled"),
            ("reject", "Rejected"),
        ],
    )

    @api.model
    def _get_policy_field(self):
        res = super(BadDebtAllowance, self)._get_policy_field()
        policy_field = [
            "confirm_ok",
            "approve_ok",
            "done_ok",
            "cancel_ok",
            "reject_ok",
            "restart_ok",
            "restart_approval_ok",
            "manual_number_ok",
        ]
        res += policy_field
        return res

    @api.onchange("type_id")
    def onchange_journal_id(self):
        self.journal_id = False
        if self.type_id:
            self.journal_id = self.type_id.journal_id.id

    @api.onchange("type_id")
    def onchange_expense_account_id(self):
        self.expense_account_id = False
        if self.type_id:
            self.expense_account_id = self.type_id.expense_account_id.id

    @api.onchange("type_id")
    def onchange_allowance_account_id(self):
        self.allowance_account_id = False
        if self.type_id:
            self.allowance_account_id = self.type_id.allowance_account_id.id

    def _prepare_move_line_criteria(self):
        self.ensure_one()
        result = [
            ("partner_id", "=", self.partner_id.id),
            ("full_reconcile_id", "=", False),
            ("account_id", "in", self.type_id.allowed_account_ids.ids),
        ]

        if not self.type_id.use_min_days_due and not self.type_id.use_max_days_due:
            result += [
                ("days_overdue", ">", 0),
            ]

        if self.type_id.use_min_days_due:
            result += [
                ("days_overdue", ">=", self.type_id.min_days_due),
            ]

        if self.type_id.use_max_days_due:
            result += [
                ("days_overdue", "<=", self.type_id.max_days_due),
            ]

        return result

    def _prepare_detail_data(self, move_line):
        self.ensure_one()
        percentage = self._get_allowance_percentage(move_line)
        return {
            "bad_debt_id": self.id,
            "source_move_line_id": move_line.id,
            "days_overdue": move_line.days_overdue,
            "amount_residual": move_line.amount_residual,
            "amount_residual_currency": move_line.amount_residual_currency,
            "allowance_percentage": percentage,
        }

    def _get_allowance_percentage(self, move_line):
        self.ensure_one()
        Percentage = self.env["bad_debt_allowance_type.percentage"]
        criteria = [
            ("type_id", "=", self.type_id.id),
            ("min_day_overdue", "<=", move_line.days_overdue),
            ("max_day_overdue", ">=", move_line.days_overdue),
        ]
        percentages = Percentage.search(criteria)

        if len(percentages) == 0:
            err_msg = _("No percentage configuration found")
            raise UserError(err_msg)

        return percentages[0].percentage

    def action_populate(self):
        for record in self:
            record._populate()

    def _populate(self):
        self.ensure_one()
        self.detail_ids.unlink()
        ML = self.env["account.move.line"]
        Detail = self.env["bad_debt_allowance.detail"]
        self.detail_ids.unlink()
        lines = ML.search(self._prepare_move_line_criteria())
        if len(lines) > 0:
            for line in lines:
                Detail.create(self._prepare_detail_data(line))

    def _prepare_account_move_data(self):
        self.ensure_one()
        data = {
            "name": self.name,
            "journal_id": self.journal_id.id,
            "date": self.date,
        }
        return data

    @ssi_decorator.post_done_action()
    def _create_accounting_entry(self):
        self.ensure_one()
        Move = self.env["account.move"].with_context(check_move_validity=False)
        move = Move.create(self._prepare_account_move_data())

        for detail in self.detail_ids:
            detail._create_accounting_entry(move)

        move.action_post()

        self.write({"move_id": move.id})

    @ssi_decorator.post_cancel_action()
    def _delete_accounting_entry(self):
        self.ensure_one()
        if not self.move_id:
            return True

        if self.move_id:
            self.move_id.with_context(force_delete=True).unlink()

        self.write({"move_id": False})
