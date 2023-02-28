import datetime

from odoo import api, fields, models, _

from odoo.exceptions import UserError, ValidationError


class Picking(models.Model):
    _inherit = "stock.picking"

    # [UC-11] - To calculate stock moves
    quality_check_count = fields.Integer(string="Quality Check", compute="_get_quality_checks")
    quality_check_id = fields.Many2one(comodel_name='quality.check.basic', compute='_get_quality_checks', copy=False)

    # To bypass the Before QC
    bypass_qc = fields.Boolean(string="Bypass Quality Check?", default=False)
    bypass_comment = fields.Text(string="Comment")
    bypassed_by = fields.Many2one(comodel_name='res.users', string="Bypassed By", readonly=True)

    # To Map Quality fail record to capture the Garment Return
    quality_fail_line = fields.Many2one(comodel_name="quality.check.line.info")

    # Before Wash quality check return
    bw_return_lot = fields.Many2one(comodel_name="stock.production.lot", string="Before wash lot id")

    @api.onchange('bypass_qc')
    def set_bypass_user(self):
        """When user click to bypass the before QC, map the user who did the change"""
        if self.bypass_qc:
            self.bypassed_by = self.env.user

    @api.depends("picking_type_id")
    def _afterwash_process(self):
        for record in self:
            if record.picking_type_id:
                if record.picking_type_id.aw_wash_to_logistic:
                    record.afterwash_process = True
                else:
                    record.afterwash_process = False
            else:
                record.afterwash_process = False

    # quality check button
    def before_quality_check(self):
        """Create Quality Check record"""
        view = self.env.ref('quality_check.ucwp_quality_check_form_view')
        partner = None
        if self.partner_id:
            partner = self.partner_id.id

        return {
            'res_model': 'quality.check.basic',
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'view_id': view.id,
            'target': 'current',
            'context': {
                'default_grn': self.id,
                'default_partner_id': partner,
                'default_quality_point': 'before_wash',
            },
        }

    # [UC-11]
    def _get_quality_checks(self):
        """Calculate the number of quality checks available for the GRN and those IDs"""
        quality_checks = self.env['quality.check.basic'].search([('grn', '=', self.id)], limit=1)
        if quality_checks:
            self.quality_check_count = 1
            self.quality_check_id = quality_checks.id
        else:
            self.quality_check_count = 0
            self.quality_check_id = None

    def action_view_quality_count(self):
        view = self.env.ref('quality_check.ucwp_quality_check_form_view')
        record = self.env['quality.check.basic'].search([('grn', '=', self.id)], limit=1)

        return {
            'res_model': 'quality.check.basic',
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'view_id': view.id,
            'res_id': record.id,
            'target': 'current',
        }

    def write(self, vals):
        if 'bypass_qc' in vals:
            if vals['bypass_qc']:
                vals['bypassed_by'] = self.env.user
        return super(Picking, self).write(vals)


class StockMove(models.Model):
    _inherit = "stock.move"

    bw_return_lot = fields.Many2one(comodel_name="stock.production.lot", string="Before wash lot id")
