from odoo import api, fields, models, _
from datetime import datetime, date, timezone
import pytz
from odoo.exceptions import AccessError, UserError, ValidationError


class MrpProduction(models.Model):
    _inherit = 'mrp.production'

    quality_check_count = fields.Integer(string='Quality Check Count', compute='_get_quality_checks')
    quality_check_id = fields.Many2one(comodel_name='quality.check.basic', string="Quality Check ID",
                                       compute='_get_quality_checks', copy=False)

    def _get_quality_checks(self):
        """Calculate the number of quality checks available for the MO and those IDs"""
        quality_checks = self.env['quality.check.basic'].search([('manufacture_order', '=', self.id)], limit=1)
        if quality_checks:
            self.quality_check_count = 1
            self.quality_check_id = quality_checks.id
        else:
            self.quality_check_count = 0
            self.quality_check_id = None

    def action_view_quality_check(self):
        if self.quality_check_count == 1:
            quality_record_id = self.quality_check_id.id
            view = self.env.ref('quality_check.ucwp_quality_check_form_view')
            return {
                'res_model': 'quality.check.basic',
                'type': 'ir.actions.act_window',
                'view_mode': 'form',
                'view_id': view.id,
                'target': 'current',
                'res_id': quality_record_id
            }

    def after_quality_check(self):
        """Popup quality check view"""
        view = self.env.ref('quality_check.ucwp_quality_check_form_view')

        return {
            'res_model': 'quality.check.basic',
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'view_id': view.id,
            'target': 'current',
            'context': {
                'default_manufacture_order': self.id,
                'default_quality_point': 'after_wash',
            },
        }
