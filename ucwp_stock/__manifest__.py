# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
{
    'name': 'Inventory',
    'version': '1',
    'website': 'https://www.subtletechs.com/',
    'author': 'Subtle Technologies (Pvt) Ltd',
    'depends': [
        'base',
        'stock',
        'mail',
        'sale_management',
        'product_expiry',
        'report_xlsx',
        'price_estimate',
        'purchase',
    ],
    'data': [
        'data/product_data.xml',
        'data/sequence_data.xml',
        'data/style_expire_cron.xml',
        'data/stock_move_line_barcode.xml',
        'security/ir.model.access.csv',
        'views/product_template.xml',
        'views/stock_move.xml',
        'views/sale_order.xml',
    ],

    'installable': True,
    'application': True,
}
