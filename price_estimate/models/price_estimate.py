from odoo import api, fields, models, _, tools


class PreCosting(models.Model):
    _name = "pre.costing"
    _inherit = ['mail.thread']
    _description = "Price Estimate"

    name = fields.Char(string="Number", default="New", readonly=True)
    product_id = fields.Many2one(comodel_name="product.template", string="Product", required=True, tracking=True)
    # domain="[('is_garment', '=', True)]",
    res_currency = fields.Many2one(comodel_name='res.currency', string="Currency Type", required=True, tracking=True)
    total_wet_line_costs = fields.Monetary(currency_field='res_currency', string="Total Price(Wet)", readonly=True,
                                           store=True,
                                           compute="_calculate_total_line_costs")
    total_dry_line_costs = fields.Monetary(currency_field='res_currency', string="Total Price(Dry)", readonly=True,
                                           store=True,
                                           compute="_calculate_total_line_costs")
    total_cost_of_wet_and_dry = fields.Monetary(currency_field='res_currency', string="Total Price", readonly=True,
                                                store=True,
                                                compute="_calculate_total_line_costs")
    gsn = fields.Float(string="GSN", tracking=True)
    fabric_composition = fields.Text(string="Fabric Composition", tracking=True)
    state = fields.Selection([('draft', 'Draft'), ('confirm', 'Confirm')], string="Status", default="draft")
    # For wet process
    pre_costing_wet_process_lines = fields.One2many(comodel_name="pre.costing.lines", inverse_name="pre_costing_id",
                                                    string="Wet Process Lines")
    # For dry process
    pre_costing_dry_process_lines = fields.One2many(comodel_name="pre.costing.lines", inverse_name="pre_costing_dry_id",
                                                    string="Dry Process Lines")
    buyer = fields.Many2one(comodel_name="res.partner", string="Buyer", store=True, tracking=True)
    wash_type = fields.Many2one(comodel_name="price.estimate.wash.type", string="Wash Type", tracking=True)
    garment_type = fields.Many2one(comodel_name="garment.type", string="Garment Type", tracking=True)

    # UCWP|IMP|-00080 Add Pre Costing to CRM
    order_qty = fields.Float(string="Order Quantity(PCS)", tracking=True)
    expt_start_date = fields.Datetime(string="Expected Start Date", tracking=True)
    customer = fields.Many2one(comodel_name="res.partner", string="Customer", required=True, store=True, tracking=True)
    wash_duration = fields.Float(string="Wash Duration", tracking=True)
    rep_code = fields.Many2one(comodel_name="rep.code", string="Rep Code", tracking=True)

    opportunity_count = fields.Integer(string="Opportunity", compute="_get_opportunity")

    company_name = fields.Many2one(comodel_name="res.partner", string="Company", tracking=True)
    rate_per_piece = fields.Float(string="Rate Per Piece(US$)", tracking=True)
    uni_id = fields.Many2one(comodel_name="uom.uom", string="UoM", tracking=True)
    weight = fields.Float(string="Weight of Garment", tracking=True)
    payment_term_id = fields.Many2one('account.payment.term', string='Payment Terms', tracking=True)
    accepted_damage = fields.Float(string="Accepted Damage %", tracking=True)
    avg_per_day = fields.Integer(string="Average per day(PCS)", tracking=True)
    size_range = fields.Char(string="Size Range", tracking=True)

    @api.model
    def create(self, vals):
        """Set sequence"""
        sequence = self.env['ir.sequence'].next_by_code('pre.costing') or _('New')
        vals['name'] = sequence
        return super(PreCosting, self).create(vals)

    def action_confirm(self):
        """Change state to Confirm"""
        self.write({'state': 'confirm'})

    def action_draft(self):
        self.write({'state': 'draft'})

    @api.onchange('customer')
    def _set_company(self):
        if self.customer:
            if self.customer.parent_id:
                self.company_name = self.customer.parent_id.id
            else:
                self.company_name = False

    @api.depends('pre_costing_wet_process_lines.price', 'pre_costing_dry_process_lines.price')
    def _calculate_total_line_costs(self):
        """Calculate Total for Wet process, Dry process and Total cost of wet & dry processes"""
        for record in self:
            # Total cost for wet process
            total_wet_line_costs = 0
            for pre_costing_wet_process_line in self.pre_costing_wet_process_lines:
                total_wet_line_costs += pre_costing_wet_process_line.price
            record.total_wet_line_costs = total_wet_line_costs
            # Total cost for dry process
            total_dry_line_cost = 0
            for pre_costing_dry_process_line in self.pre_costing_dry_process_lines:
                total_dry_line_cost += pre_costing_dry_process_line.price
            record.total_dry_line_costs = total_dry_line_cost
            # Total cost for wet and dry processes
            record.total_cost_of_wet_and_dry = record.total_wet_line_costs + record.total_dry_line_costs

    @api.onchange('pre_costing_wet_process_lines', 'pre_costing_dry_process_lines', 'res_currency')
    def set_currency_type(self):
        """Set currency type for wet process & dry process tabs"""
        if self.res_currency:
            self.pre_costing_wet_process_lines.res_currency = self.res_currency
            self.pre_costing_dry_process_lines.res_currency = self.res_currency

    @api.onchange('uni_id')
    def _onchange_uni_id(self):
        uom_kg = self.env.ref('uom.product_uom_kgm').id
        uom_pcs = self.env.ref('price_estimate.product_uom_pcs').id
        uom_yds = self.env.ref('price_estimate.product_uom_yds').id
        uom_m = self.env.ref('uom.product_uom_meter').id
        uom_ids = [uom_kg, uom_pcs, uom_yds, uom_m]
        return {'domain': {'uni_id': [('id', 'in', uom_ids)]}}

    def action_send_email(self):
        ir_model_data = self.env['ir.model.data']
        try:
            template_id = \
                ir_model_data._xmlid_lookup('price_estimate.price_estimate_report_email_template')[2]
        except ValueError:
            template_id = False

        try:
            compose_form_id = ir_model_data._xmlid_lookup('mail.email_compose_message_wizard_form')[2]
        except ValueError:
            compose_form_id = False
        ctx = dict(self.env.context or {})
        ctx.update({
            'default_model': 'pre.costing',
            'active_model': 'pre.costing',
            'active_id': self.ids[0],
            'default_res_id': self.ids[0],
            'default_use_template': bool(template_id),
            'default_template_id': template_id,
            'default_composition_mode': 'comment',
            'force_email': True,
        })

        lang = self.env.context.get('lang')
        if {'default_template_id', 'default_model', 'default_res_id'} <= ctx.keys():
            template = self.env['mail.template'].browse(ctx['default_template_id'])
            if template and template.lang:
                lang = template._render_lang([ctx['default_res_id']])[ctx['default_res_id']]

        self = self.with_context(lang=lang)
        ctx['model_description'] = _('Price Estimate')

        """Change stage when sent price estimate"""
        if self.opportunity_no:
            stage = self.env['crm.stage'].search([('name', '=', 'Price Estimate')])
            self.opportunity_no.write({'stage_id': stage.id})

        return {
            'name': _('Compose Email'),
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'mail.compose.message',
            'views': [(compose_form_id, 'form')],
            'view_id': compose_form_id,
            'target': 'new',
            'context': ctx,
        }

    def _get_opportunity(self):
        crm_stages = self.env['crm.lead'].search([('partner_id', '=', self.customer.id),
                                                  ('type', '=', 'opportunity')])
        if crm_stages:
            self.opportunity_count = len(crm_stages)
        else:
            self.opportunity_count = 0

    def action_view_opportunity(self):
        crm_stages = self.env['crm.lead'].search([('partner_id', '=', self.customer.id),
                                                  ('type', '=', 'opportunity')])
        if crm_stages:
            if len(crm_stages) > 1:
                form_view = self.env.ref('crm.crm_lead_view_form').id
                tree_view = self.env.ref('crm.crm_case_tree_view_oppor').id
                return {
                    'name': 'Opportunities',
                    'res_model': 'crm.lead',
                    'type': 'ir.actions.act_window',
                    'view_mode': 'list,form',
                    'views': [[tree_view, 'list'], [form_view, 'form']],
                    'target': 'current',
                    'domain': [('id', 'in', crm_stages.ids)],

                }
            if len(crm_stages) == 0:
                form_view = self.env.ref('crm.crm_lead_view_form').id
                return {
                    'res_model': 'crm.lead',
                    'type': 'ir.actions.act_window',
                    'view_mode': 'form',
                    'view_id': form_view,
                    'res_id': crm_stages.id,
                    'target': 'current',
                }


class PreCostingLines(models.Model):
    _name = "pre.costing.lines"
    _description = "Pre Costing Lines"

    # Wet process
    pre_costing_id = fields.Many2one(comodel_name="pre.costing", string="Wet Pre Costing ID")
    # Dry process
    pre_costing_dry_id = fields.Many2one(comodel_name="pre.costing", string="Dry Pre Costing ID")
    process_type = fields.Selection([('wet', 'Wet Process'), ('dry', 'Dry Process')], string="Process Type")
    operation = fields.Many2one(comodel_name="price.estimate.workcenter", string="Operation", required=True,
                                domain="[('process_type', '=', process_type)]")
    res_currency = fields.Many2one(comodel_name='res.currency')
    cost = fields.Monetary(currency_field='res_currency', string="Cost", required=True)
    pieces_for_hour_actual = fields.Integer(string="Actual No of Pieces for Hour")
    pieces_for_hour_target = fields.Integer(string="Target No of Pieces for Hour")
    price = fields.Monetary(currency_field='res_currency', string="Price", store=True,
                            compute="_calculate_cost")

    @api.depends('cost')
    def _calculate_cost(self):
        """Calculate total per line"""
        for record in self:
            record.price = record.cost


class PriceEstimateWashType(models.Model):
    _name = "price.estimate.wash.type"
    _description = "Wash Type"

    name = fields.Char(string="Wash Type")


class PriceEstimateWorkCenter(models.Model):
    _name = "price.estimate.workcenter"
    _description = "Work Center"

    name = fields.Char(string="Operation", required=True)
    process_type = fields.Selection([('dry', 'Dry Process'), ('wet', 'Wet Process')], string="Process Type")


class GarmentType(models.Model):
    _name = "garment.type"

    name = fields.Char(string="Garment Type")


class RepCode(models.Model):
    _name = 'rep.code'
    _description = "Rep Code"

    name = fields.Char(string="Rep Code")
