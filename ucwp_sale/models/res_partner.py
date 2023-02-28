from odoo import api, fields, models, _


class Partner(models.Model):
    _inherit = 'res.partner'

    payment_method = fields.Selection([('cod', 'Cash On Delivery'), ('credit', 'Credit')], string='Payment Type')
    geo_location = fields.Selection([('local', 'Local'), ('foreign', 'Foreign')], string='Customer From')
    credit_limit_available = fields.Boolean(string="Credit Limit Available", default=False)
    credit_limit = fields.Monetary(string="Credit Limit")
    customer_currency_id = fields.Many2one(comodel_name="res.currency", default=lambda self: self.env.company.currency_id, string="Customer Currency")
    available_credit_limit = fields.Monetary(currency_field='currency_id', string="Available Credits",
                                             compute='compute_available_credit_limit')
    total_pending_payments = fields.Monetary(currency_field='currency_id', string="Total Pending Payments",
                                             compute='compute_total_pending')

    """----------------------Related to Credit Limit calculation from Account Package----------------------------"""
    unpaid_invoices = fields.One2many('account.move', compute='_compute_unpaid_invoices')
    unreconciled_aml_ids = fields.One2many('account.move.line', compute='_compute_unreconciled_aml_ids')
    total_due = fields.Monetary(compute='_compute_total_due')

    """---------------------------VAT  / SVAT / NBT Reg numbers-------------------------------"""
    svat_id = fields.Char('SVAT ID')
    nbt_id = fields.Char('NBT ID')

    """-------------------------Supplier  /  Customer Separation-------------------------------"""
    is_customer = fields.Boolean(string="Is Customer ?", default=False)
    is_supplier = fields.Boolean(string="Is Supplier ?", default=False)

    # UCWP|IMP|-00058 Credit Note Value Limit Creation
    credit_note_percentage = fields.Float(string="Credit Note Percentage")

    def _compute_unpaid_invoices(self):
        """Get unpaid customer invoices"""
        for record in self:
            record.unpaid_invoices = self.env['account.move'].search([
                ('company_id', '=', self.env.company.id),
                ('commercial_partner_id', '=', record.id),
                ('state', '=', 'posted'),
                ('payment_state', 'in', ('not_paid', 'partial')),
                ('move_type', 'in', self.env['account.move'].get_sale_types())
            ]).filtered(lambda inv: not any(inv.line_ids.mapped('blocked')))

    @api.depends('invoice_ids')
    @api.depends_context('company', 'allowed_company_ids')
    def _compute_unreconciled_aml_ids(self):
        values = {
            read['partner_id'][0]: read['line_ids']
            for read in self.env['account.move.line'].read_group(
                domain=self._get_unreconciled_aml_domain(),
                fields=['line_ids:array_agg(id)'],
                groupby=['partner_id']
            )
        }
        for partner in self:
            partner.unreconciled_aml_ids = values.get(partner.id, False)

    def _get_unreconciled_aml_domain(self):
        return [
            ('reconciled', '=', False),
            ('account_id.deprecated', '=', False),
            ('account_id.internal_type', '=', 'receivable'),
            ('move_id.state', '=', 'posted'),
            ('partner_id', 'in', self.ids),
            ('company_id', '=', self.env.company.id),
        ]

    @api.depends_context('company', 'allowed_company_ids')
    def _compute_total_due(self):
        """
        Compute the fields 'total_due'
        """
        today = fields.Date.context_today(self)
        for record in self:
            total_due = 0
            total_overdue = 0
            for aml in record.unreconciled_aml_ids:
                if aml.company_id == self.env.company and not aml.blocked:
                    amount = aml.amount_residual
                    total_due += amount
                    is_overdue = today > aml.date_maturity if aml.date_maturity else today > aml.date
                    if is_overdue:
                        total_overdue += amount
            record.total_due = total_due

    """------------------End - From Core Account Followups----------------------"""

    def compute_total_pending(self):
        for record in self:
            if record.credit_limit_available:
                record.total_pending_payments = record.total_due
            else:
                record.total_pending_payments = 0

    def compute_available_credit_limit(self):
        for record in self:
            if record.credit_limit_available:
                record.available_credit_limit = record.credit_limit - record.total_due
            else:
                record.available_credit_limit = 0


