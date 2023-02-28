# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
{
    'name': 'CRM',
    'version': '1',
    'website': 'https://www.subtletechs.com/',
    'author': 'Subtle Technologies (Pvt) Ltd',
    'depends': [
        'base',
        'mail',
        'crm',
        'stock',
        'price_estimate',
    ],
    'data': [
        'data/sequence_data.xml',
        'views/crm_lead_views.xml',
        'security/ir.model.access.csv',
    ],

    'installable': True,
    'application': True,
}
