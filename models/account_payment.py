from odoo import models, fields, api, _
import odoo.addons.decimal_precision as dp
from datetime import datetime, timedelta
from odoo.exceptions import UserError


class AccountPayment(models.Model):
    _inherit = 'account.payment'

    cashflow_trace_account_id = fields.Many2one('account.account', string="Direct C/F Account")