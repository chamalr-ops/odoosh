# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
{
    'name': 'Price Estimate',
    'version': '1',
    'website': 'https://www.subtletechs.com/',
    'author': 'Subtle Technologies (Pvt) Ltd',
    'depends': [
        'base',
        'mail',
        'report_xlsx',
        'crm',
        'account',
        'stock',
    ],
    'data': [
        'security/ir.model.access.csv',
        'report/price_estimate.xml',
        'data/price_estimate_email_template.xml',
        'data/price_estimate_data.xml',
        'data/uom_data.xml',
        'views/price_estimate_view.xml',
    ],

    'installable': True,
    'application': True,
}
