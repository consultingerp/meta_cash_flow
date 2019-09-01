{
    "name": "Meta Cash Flow",
    "category": 'Accounting',
    "summary": """
        This module will help to create report for company cash flow for different activities.
        """,
    "description": """This module will help to create report for company cash flow for different activities.""",
    "sequence": 1,
    "version": '10.0.1.0',
    "author": "Metamorphosis",
    'license': 'OPL-1',
    'company': 'Metamorphosis Limited',
    'website': 'metamorphosis.com.bd',
    "depends": ['account','custom_report'],
    "data": [
        'views/cash_flow_data.xml',
        'views/cash_flow_wizard.xml',
        'views/cash_flow_report.xml',
        'views/account_payment.xml',
    ],
    'icon': "/meta_cash_flow/static/description/icon.png",
    "images": ["static/description/banner.png"],
    "installable": True,
    "application": True,
    "auto_install": False,
    'price':200.0,
    'currency':'EUR',     
}

