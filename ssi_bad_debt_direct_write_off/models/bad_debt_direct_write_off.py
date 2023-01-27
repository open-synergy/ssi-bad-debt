# Copyright 2023 OpenSynergy Indonesia
# Copyright 2023 PT. Simetri Sinergi Indonesia
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo import api, fields, models

from odoo.addons.ssi_decorator import ssi_decorator


class BadDebtDirectWriteOff(models.Model):
    _name = "bad_debt_direct_write_off"
    _inherit = [
        "mixin.transaction_confirm",
        "mixin.transaction_done",
        "mixin.transaction_cancel",
        "mixin.company_currency",
    ]

    date = fields.Date(
        string="Date",
        required=True,
    )
    type_id = fields.Many2one(
        string="Type",
        comodel_name="bad_debt_direct_write_off_type",
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
    expense_account_id = fields.Many2one(
        string="Expense Account",
        comodel_name="account.account",
        required=True,
        ondelete="restrict",
    )
    move_id = fields.Many2one(
        string="Move",
        comodel_name="account.move",
        readonly=True,
    )
    detail_ids = fields.One2many(
        string="Detail",
        comodel_name="bad_debt_direct_write_off.detail",
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

    @api.model
    def _get_policy_field(self):
        res = super(BadDebtDirectWriteOff, self)._get_policy_field()
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
        if self.type_id:
            self.journal_id = self.type_id.journal_id.id

    @api.onchange("type_id")
    def onchange_expense_account_id(self):
        if self.type_id:
            self.expense_account_id = self.type_id.expense_account_id.id

    def _prepare_move_line_criteria(self):
        self.ensure_one()
        return [
            ("partner_id", "=", self.partner_id.id),
            ("days_overdue", ">=", self.type_id.min_days_due),
            ("days_overdue", "<=", self.type_id.max_days_due),
            ("full_reconcile_id", "=", False),
            ("account_id", "in", self.type_id.allowed_account_ids.ids),
        ]

    def _prepare_detail_data(self, move_line_id):
        self.ensure_one()
        return {"bad_debt_id": self.id, "source_move_line_id": move_line_id}

    def action_populate(self):
        obj_move_line = self.env["account.move.line"].with_context(
            check_move_validity=False
        )
        obj_detail = self.env["bad_debt_direct_write_off.detail"].with_context(
            check_move_validity=False
        )
        for record in self.sudo():
            record.detail_ids.unlink()
            move_line_ids = obj_move_line.search(record._prepare_move_line_criteria())
            if move_line_ids:
                for move_line in move_line_ids:
                    obj_detail.create(record._prepare_detail_data(move_line.id))

    def _prepare_account_move_data(self):
        self.ensure_one()
        data = {
            "name": self.name,
            "journal_id": self.journal_id.id,
            "date": self.date,
        }
        return data

    def _prepare_expense_move_line_data(self):
        self.ensure_one()
        data = {
            "move_id": self.bad_debt_id.move_id,
            "account_id": self.bad_debt_id.expense_account_id.id,
            "name": self.source_move_line_id.move_id.name,
            "debit": self.amount_residual,
            "credit": 0,
            "currency_id": self.source_move_line_id.currency_id.id,
            "amount_currency": self.amount_residual_currency,
        }
        return data

    @ssi_decorator.post_done_action()
    def _create_accounting_entry(self):
        self.ensure_one()
        self._create_account_move()
        for line in self.detail_ids:
            line._create_account_move_line()
        self.move_id.action_post()
        return True

    def _create_account_move(self):
        self.ensure_one()
        if not self.move_id:
            obj_account_move = self.env["account.move"].with_context(
                check_move_validity=False
            )
            move = obj_account_move.create(self._prepare_account_move_data())
            self.move_id = move

    def _create_account_move_line(self):
        self.ensure_one()
        obj_line = self.env["account.move.line"].with_context(check_move_validity=False)
        line = obj_line.create(self._prepare_expense_move_line_data())
        self.expense_move_line_id = line

    @ssi_decorator.post_cancel_action()
    def _delete_accounting_entry(self):
        self.ensure_one()
        if self.move_id:
            self.move_id.unlink()
