from datetime import datetime, timedelta
from itertools import groupby
import json

from odoo import api, fields, models, SUPERUSER_ID, _
from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.osv import expression
from odoo.tools import float_is_zero, html_keep_url, is_html_empty


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    po_no = fields.Many2one(comodel_name="po.number", string="PO No")


class PONumber(models.Model):
    _name = "po.number"

    name = fields.Char(string="PO")
