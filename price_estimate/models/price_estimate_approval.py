from odoo import api, fields, models, _, tools


class PreCostingApproval(models.Model):
    _name = "pre.costing.approval"
    _description = "Approval For Pre Costing"
    _rec_name = "quotation"

    quotation = fields.Many2one(comodel_name="sale.order", string="Quotation", domain="[('state', '=', 'draft')]")
    state = fields.Selection([('waiting', 'Waiting for Approval'), ('approved', 'Approved')], string="State",
                             default='waiting')

    def action_approve(self):
        self.write({'state': 'approved'})
        self.quotation.is_approved = True

    def action_wait(self):
        self.write({'state': 'waiting'})
        self.quotation.is_approved = False


class PreCostingApprovalWizard(models.TransientModel):
    _name = "pre.costing.approval.wizard"

    quotation = fields.Many2one(comodel_name="sale.order", string="Quotation", domain="[('state', '=', 'draft')]")
    need_to_approve_products = fields.Char(string="Need to approve")
    warning = fields.Text(readonly=True)

    def create_approval(self):
        """Create Pre Costing Approval record"""
        self.env['pre.costing.approval'].create({
            'quotation': self.quotation.id,
            'state': 'waiting',
        })

    @api.onchange('need_to_approve_products')
    def _warning(self):
        self.warning = 'Sale order price of ' + str(
            self.need_to_approve_products) + ' product/s is/are less than the agreed price on pre-costing'
