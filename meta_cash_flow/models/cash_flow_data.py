from openerp import models, fields, api, _
import openerp.addons.decimal_precision as dp
from datetime import datetime, timedelta
from odoo.exceptions import UserError


class CashFlowData(models.Model):
    _name = 'cash.flow.data'
    _order = 'layer asc'

    label = fields.Char('Lebel')
    ac_type = fields.Char('Type')
    account_id = fields.Many2one('account.account',string='Cash & bank')
    currency_id = fields.Many2one('res.currency', string='Currency', default=lambda self: self.env.user.company_id.currency_id.id)
    layer = fields.Integer("Layer")
    credit = fields.Float(string='Credit')
    debit = fields.Float(string='Debit')
    balance = fields.Float(string='Balance')
    start_date = fields.Date('Start Date')
    end_date = fields.Date('Start Date')


    @api.multi
    def get_value(self, value):
        if value in [100,200,300]:
            return 1
        elif value in [110,120,210,220,310,320]:
            return 2
        else:
            return 3


    @api.multi
    def calculate_opening_and_closing(self):
        all_bank_and_cash_account = self.env['account.account'].search([['user_type_id','in' ,['Bank and Cash','Credit Card',]],['company_id','=',self.env.user.company_id.id]])
        bank_cash = dict()
        bank_cash['opening'] = list()
        bank_cash['closing'] = list()
        total_opening = 0
        total_closing = 0
        for account in all_bank_and_cash_account:
            all_move_line = self.env['account.move.line'].search([['account_id','=',account.id],['date','<',self.start_date]])
            total = 0
            for move_line in all_move_line:
                total += (move_line.debit - move_line.credit)
            total_opening += total
            # if total>0:
            bank_cash['opening'].append({'code':account.code,'name':account.name,'balance':total})

            all_move_line = self.env['account.move.line'].search([['account_id','=',account.id],['date','<=',self.end_date]])
            total = 0
            for move_line in all_move_line:
                total += (move_line.debit - move_line.credit)
            total_closing += total
            # if total>0:
            bank_cash['closing'].append({'code':account.code,'name':account.name,'balance':total})

        bank_cash['opening'].append({'code':'Total','balance':total_opening})
        bank_cash['closing'].append({'code':'Total','balance':total_closing})
        bank_cash['opening_total']=total_opening
        bank_cash['closing_total']=total_closing

        return bank_cash
