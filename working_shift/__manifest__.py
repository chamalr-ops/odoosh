# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
{
    'name': 'Working Shift',
    'version': '15.0.0',
    'website': 'https://www.subtletechs.com/',
    'author': 'Subtle Technologies (Pvt) Ltd',
    'depends': [
        'base',
        'mrp',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/working_shift.xml',
    ],

    'installable': True,
    'application': False,
}
