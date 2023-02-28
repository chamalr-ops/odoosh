# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
{
    'name': 'Quality Check for Garment',
    'version': '1.0.0',
    'website': 'https://www.subtletechs.com/',
    'author': 'Subtle Technologies (Pvt) Ltd',
    'depends': [
        'base',
        'stock',
        'mrp',
        'mail',
        'report_xlsx',
    ],
    'data': [
        'report/quality_check_report.xml',
        'data/sequence_data.xml',
        'data/email_templates.xml',
        'security/ir.model.access.csv',
        'views/defects.xml',
        'views/mrp_production_view.xml',
        'views/quality_check_view.xml',
        'views/stock_picking_view.xml',
    ],

    'installable': True,
    'application': True,
}
