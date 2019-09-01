from openerp import models, fields, api, _
import openerp.addons.decimal_precision as dp
from datetime import datetime, timedelta
from odoo.exceptions import UserError


class CashFlowWizard(models.Model):
    _name = 'cash.flow.wizard'

    from_date = fields.Date('From Date', default=lambda self: fields.datetime.now())
    to_date = fields.Date('To Date', default=lambda self: fields.datetime.now())

    entry_post_status = fields.Selection([('posted','All Posted Entries'),('draft','All Entries')], string="Entry Type", default='posted')

    # @api.multi
    # def verify_account_type(self,journal_entrires):
    #     for journal_entry in journal_entrires:
    #         for line in journal_entry.line_ids:
    #             if line.account_id.tag_ids:
    #                 return line.account_id

    @api.multi
    def verify_account_type_without_tax(self, journal_entries, amount):
        account_vs_balance_list = list()
        tax_account_list = list()
        
        all_tax = self.env['account.tax'].search([])
        for item in all_tax:
            tax_account_list.append(item.account_id.id)

        for journal_entry in journal_entries:
            for line in journal_entry.line_ids:
                    
                if line.account_id.tag_ids and line.account_id.id not in tax_account_list:
                    balance = amount
                    account_vs_balance_list.append([line.account_id, balance])
                    if account_vs_balance_list:
                        return account_vs_balance_list
                        
        return account_vs_balance_list
                    

    @api.multi
    def verify_account_type(self, journal_entries):
        account_vs_balance_list = list()

        for journal_entry in journal_entries:
            for line in journal_entry.line_ids:
                if line.account_id.tag_ids:
                    balance = abs(line.debit-line.credit)
                    account_vs_balance_list.append([line.account_id, balance])

        return account_vs_balance_list

    @api.multi
    def get_account_info(self,ac_id):
        account_id = self.env['account.account'].browse(ac_id)
        return str(account_id.code)+" "+str(account_id.name)

    @api.multi
    def get_layer_number(self, activities,status):
        layer_count = dict()
        layer_count.update({'Operating Activities':100,'Financing Activities':200, 'Investing & Extraordinary Activities':300, 'cashin':10, 'cashout':20})
        
        return layer_count[activities] + layer_count[status] + 1



    @api.multi
    def done(self):
        self.env.cr.execute(""" TRUNCATE TABLE cash_flow_data ; """)
        all_bank_and_cash_account = self.env['account.account'].search([['user_type_id', 'in' ,['Bank and Cash','Credit Card',]],['company_id','=',self.env.user.company_id.id]])
        
        cash_flow_group = dict()
        cash_flow_group.update( {'Operating Activities' : {'value':0,'cashin':0,'cashout':0}} )
        cash_flow_group.update( {'Financing Activities' : {'value':0,'cashin':0,'cashout':0}} )
        cash_flow_group.update( {'Investing & Extraordinary Activities' : {'value':0,'cashin':0,'cashout':0}} )

        cash_flow_account = dict()
        cash_flow_account.update( {'Operating Activities' : {'cashin':{0:0},'cashout':{0:0}}} )
        cash_flow_account.update( {'Financing Activities' : {'cashin':{0:0},'cashout':{0:0}}} )
        cash_flow_account.update( {'Investing & Extraordinary Activities' : {'cashin':{0:0},'cashout':{0:0}}} )

        all_journal_item = self.env['account.move.line'].search([['date','>=',self.from_date],['date','<=',self.to_date],['company_id','=',self.env.user.company_id.id]])
        
    
        if self.entry_post_status == 'posted':
            journal_entry_posting_status = ['posted']
        else:
            journal_entry_posting_status = ['posted','draft']
            
        bc_journal_item = list()
        for journal_item in all_journal_item:
            
            if journal_item.account_id.id in all_bank_and_cash_account.ids:
                # print journal_item.account_id.name
                journal_entry = journal_item.move_id
                if journal_entry.state in journal_entry_posting_status:
                    if journal_item.payment_id:
                        payment_id = journal_item.payment_id
                    else:
                        payment_id = False
                    # print journal_item.account_id.name
                    # account_id = self.verify_account_type(journal_entry)
                    account_vs_balance_list = list()
                    account_vs_balance_list = self.verify_account_type(journal_entry)
                    data_exist = False
                    # if account_id:
                    if len(account_vs_balance_list)>0:
                        # account_type = account_id.tag_ids
                        # if account_type:
                        data_exist = True

                    elif journal_entry.ref:
                        journal_entries_ref = self.env['account.move'].search([['name','=',journal_entry.ref],['company_id','=',self.env.user.company_id.id]])
                        if journal_entries_ref:
                            journal_entry = journal_entries_ref
                            # account_id = self.verify_account_type(journal_entry)
                            account_vs_balance_list = self.verify_account_type_without_tax(journal_entry, abs(journal_item.debit-journal_item.credit))
                            print ".....",account_vs_balance_list
                            if len(account_vs_balance_list)>0:
                                data_exist = True
                    

                    elif payment_id:
                        if payment_id.cashflow_trace_account_id and payment_id.cashflow_trace_account_id.tag_ids:
                            if payment_id.cashflow_trace_account_id:
                                account_vs_balance_list = list()
                                if payment_id.cashflow_trace_account_id.tag_ids:
                                    balance = payment_id.amount
                                    account_vs_balance_list.append([payment_id.cashflow_trace_account_id, balance])
                                    data_exist = True

                        
                    if data_exist:
                        for line_item in account_vs_balance_list:
                            account_id = line_item[0]
                            account_type = account_id.tag_ids
                            if account_type.name in cash_flow_account.keys():
                                if journal_item.debit>0:
                                    if account_id.id not in cash_flow_account[account_type.name]['cashin'].keys():
                                        cash_flow_account[account_type.name]['cashin'].update({account_id.id:0})
                                    cash_flow_account[account_type.name]['cashin'][account_id.id]+=line_item[1]
                                    
                                    #Group calculation
                                    cash_flow_group[account_type.name]['cashin']+=line_item[1]
                                    cash_flow_group[account_type.name]['value']+=line_item[1]

                                if journal_item.credit>0:
                                    if account_id.id not in cash_flow_account[account_type.name]['cashout'].keys():
                                        cash_flow_account[account_type.name]['cashout'].update({account_id.id:0})
                                    cash_flow_account[account_type.name]['cashout'][account_id.id]-=line_item[1]

                                    #Group calculation
                                    cash_flow_group[account_type.name]['cashout']-=line_item[1]
                                    cash_flow_group[account_type.name]['value']-=line_item[1]

    
        #############################################
        values1 = {'ac_type':'Operating Activities','label':'Operating Activities','layer':100,'balance':cash_flow_group['Operating Activities']['value'], 'start_date':self.from_date, 'end_date':self.to_date}
        self.env['cash.flow.data'].create(values1)
        values2 = {'ac_type':'Operating Activities','label':'Cash In','layer':110,'balance':cash_flow_group['Operating Activities']['cashin'], 'start_date':self.from_date, 'end_date':self.to_date}
        self.env['cash.flow.data'].create(values2)
        values3 = {'ac_type':'Operating Activities','label':'Cash OUT','layer':120,'balance':cash_flow_group['Operating Activities']['cashout'], 'start_date':self.from_date, 'end_date':self.to_date}
        self.env['cash.flow.data'].create(values3)

        #############################################
        values4 = {'ac_type':'Financing Activities','label':'Financing Activities','layer':200,'balance':cash_flow_group['Financing Activities']['value'], 'start_date':self.from_date, 'end_date':self.to_date}
        self.env['cash.flow.data'].create(values4)
        values5 = {'ac_type':'Financing Activities','label':'Cash In','layer':210,'balance':cash_flow_group['Financing Activities']['cashin'], 'start_date':self.from_date, 'end_date':self.to_date}
        self.env['cash.flow.data'].create(values5)
        values6 = {'ac_type':'Financing Activities','label':'Cash OUT','layer':220,'balance':cash_flow_group['Financing Activities']['cashout'], 'start_date':self.from_date, 'end_date':self.to_date}
        self.env['cash.flow.data'].create(values6)

        #############################################
        values7 = {'ac_type':'Investing & Extraordinary Activities','label':'Investing & Extraordinary Activities','layer':300,'balance':cash_flow_group['Investing & Extraordinary Activities']['value'], 'start_date':self.from_date, 'end_date':self.to_date}
        self.env['cash.flow.data'].create(values7)
        values8 = {'ac_type':'Investing & Extraordinary Activities','label':'Cash In','layer':310,'balance':cash_flow_group['Investing & Extraordinary Activities']['cashin'], 'start_date':self.from_date, 'end_date':self.to_date}
        self.env['cash.flow.data'].create(values8)
        values9 = {'ac_type':'Investing & Extraordinary Activities','label':'Cash OUT','layer':320,'balance':cash_flow_group['Investing & Extraordinary Activities']['cashout'], 'start_date':self.from_date, 'end_date':self.to_date}
        self.env['cash.flow.data'].create(values9)

        for activities in cash_flow_account.keys():
            for cash_in_out in cash_flow_account[activities].keys():
                for account in cash_flow_account[activities][cash_in_out].keys():
                    if account>0:
                        values = {
                            'ac_type':activities,
                            'label': self.get_account_info(account),
                            'account_id': account,
                            'balance': cash_flow_account[activities][cash_in_out][account],
                            'layer': self.get_layer_number(activities, cash_in_out),
                            'start_date':self.from_date, 
                            'end_date':self.to_date,
                        }
                        self.env['cash.flow.data'].create(values)

    
        docids = self.env['cash.flow.data'].search([])
        return self.env['report'].get_action(docids, 'meta_cash_flow.cash_flow_report_document')
                
