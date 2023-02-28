# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
{
    'name': 'Manufacturing',
    'version': '1',
    'website': 'https://www.subtletechs.com/',
    'author': 'Subtle Technologies (Pvt) Ltd',
    'depends': [
        'base',
        'mrp',
        'stock',
        'ucwp_stock',
    ],
    'data': [
        'data/sequence_data.xml',
        'views/mrp_production_view.xml',
        'security/ir.model.access.csv',
        'report/mrp_production_templates.xml',
        'report/mrp_bom_formula_sheet.xml',
        'report/cost_analysis_report.xml',
    ],

    'installable': True,
    'application': True,
}
