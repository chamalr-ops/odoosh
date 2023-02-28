from datetime import datetime, timedelta
from itertools import groupby
import json

from odoo import api, fields, models, SUPERUSER_ID, _
from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.osv import expression
from odoo.tools import float_is_zero, html_keep_url, is_html_empty


class SaleOrder(models.Model):
    _inherit = "sale.order"

    # garment receipt info
    garment_receipt_ids = fields.Many2many("stock.picking", string='Garment Receipt', compute="_get_garment_receipts",
                                           copy=False)
    # Actually received product quantity
    actually_received_product_qty = fields.One2many(comodel_name="actually.received.product.quantity",
                                                    inverse_name="sale_order_id",
                                                    string="Actually Received Product Quantity")
    garment_sales = fields.Boolean(string="Garment Sales", default=True)
    # Sale order type
    local_export = fields.Selection([('local', 'Local'), ('export', 'Export')], string="Local/Export")

    credit_limit_exceeded = fields.Boolean(string="Credit Limit Exceeded", compute="check_credit_block")
    credit_limit_override = fields.Boolean(string="Credit Limit Override", default=False, copy=False,
                                           tracking=True, track_visibility="onchange")
    # Add Delivery Requirement tab
    delivery_requirement = fields.One2many(comodel_name="delivery.requirement",
                                           inverse_name="delivery_requirement_sale_order_id",
                                           string="Delivery Requirement")
    # Price estimate
    price_estimate = fields.Many2one(comodel_name="pre.costing", string="Price Estimate",
                                     domain="[('state', '=', 'confirm')]")

    # Style info
    buyer = fields.Many2one(comodel_name="res.partner", string="Buyer")
    wash_type = fields.Many2one(comodel_name="price.estimate.wash.type", string="Wash Type")
    garment_type = fields.Many2one(comodel_name="garment.type", string="Garment Type")

    gsn = fields.Float(string="GSN", tracking=True)
    fabric_composition = fields.Text(string="Fabric Composition")
    order_qty = fields.Float(string="Order Quantity(PCS)")
    expt_start_date = fields.Datetime(string="Expected Start Date")
    wash_duration = fields.Float(string="Wash Duration", tracking=True)
    rep_code = fields.Many2one(comodel_name="rep.code", string="Rep Code")
    company_name = fields.Many2one(comodel_name="res.partner", string="Company")
    rate_per_piece = fields.Float(string="Rate Per Piece(US$)")
    uni_id = fields.Many2one(comodel_name="uom.uom", string="UoM")
    weight = fields.Float(string="Weight of Garment")
    payment_term_id = fields.Many2one('account.payment.term', string='Payment Terms')
    accepted_damage = fields.Float(string="Accepted Damage %")
    avg_per_day = fields.Integer(string="Average per day(PCS)")
    size_range = fields.Char(string="Size Range")

    # add new state
    state = fields.Selection(selection_add=[('customer_approved', 'Approved by Customer'), ('sale',)])

    def action_customer_approve(self):
        """ Order approved by customer """
        if self.price_estimate:
            if self.price_estimate.opportunity_no:
                stage = self.env['crm.stage'].search([('name', '=', 'Approved by Customer')])
                self.price_estimate.opportunity_no.write({'stage_id': stage.id})
        self.write({'state': 'customer_approved'})

    @api.onchange('price_estimate')
    def _onchange_price_estimate(self):
        if self.price_estimate:
            if self.price_estimate.customer:
                self.partner_id = self.price_estimate.customer
            if self.price_estimate.buyer:
                self.buyer = self.price_estimate.buyer
            if self.price_estimate.wash_type:
                self.wash_type = self.price_estimate.wash_type
            if self.price_estimate.garment_type:
                self.garment_type = self.price_estimate.garment_type
            self.garment_sales = True
            if self.price_estimate.gsn:
                self.gsn = self.price_estimate.gsn
            if self.price_estimate.fabric_composition:
                self.fabric_composition = self.price_estimate.fabric_composition
            if self.price_estimate.order_qty:
                self.order_qty = self.price_estimate.order_qty
            if self.price_estimate.expt_start_date:
                self.expt_start_date = self.price_estimate.expt_start_date
            if self.price_estimate.wash_duration:
                self.wash_duration = self.price_estimate.wash_duration
            if self.price_estimate.rep_code:
                self.rep_code = self.price_estimate.rep_code
            if self.price_estimate.company_name:
                self.company_name = self.price_estimate.company_name
            if self.price_estimate.rate_per_piece:
                self.rate_per_piece = self.price_estimate.rate_per_piece
            if self.price_estimate.uni_id:
                self.uni_id = self.price_estimate.uni_id
            if self.price_estimate.weight:
                self.weight = self.price_estimate.weight
            if self.price_estimate.payment_term_id:
                self.payment_term_id = self.price_estimate.payment_term_id
            if self.price_estimate.accepted_damage:
                self.accepted_damage = self.price_estimate.accepted_damage
            if self.price_estimate.avg_per_day:
                self.avg_per_day = self.price_estimate.avg_per_day
            if self.price_estimate.size_range:
                self.size_range = self.price_estimate.size_range

    @api.onchange('partner_id')
    def _set_company(self):
        if self.partner_id:
            if self.partner_id.parent_id:
                self.company_name = self.partner_id.parent_id.id
            else:
                self.company_name = False

    @api.onchange('uni_id')
    def _onchange_uni_id(self):
        uom_kg = self.env.ref('uom.product_uom_kgm').id
        uom_pcs = self.env.ref('price_estimate.product_uom_pcs').id
        uom_yds = self.env.ref('price_estimate.product_uom_yds').id
        uom_m = self.env.ref('uom.product_uom_meter').id
        uom_ids = [uom_kg, uom_pcs, uom_yds, uom_m]
        return {'domain': {'uni_id': [('id', 'in', uom_ids)]}}

    @api.depends('partner_id', 'amount_total', 'order_line')
    def check_credit_block(self):
        for order in self:
            if order.credit_limit_override == False:
                partner = order.partner_id
                payment_method = partner.payment_method
                credit_limit_available = partner.credit_limit_available
                credit_limit = partner.credit_limit
                if payment_method == 'credit' and credit_limit_available == True:
                    if self.amount_total > partner.available_credit_limit:
                        order.credit_limit_exceeded = True
                    else:
                        order.credit_limit_exceeded = False
                else:
                    order.credit_limit_exceeded = False
            else:
                order.credit_limit_exceeded = False

    def action_credit_override(self):
        """Override credit limit"""
        return self.write({'credit_limit_override': True, 'credit_limit_exceeded': False})

    @api.model
    def create(self, vals):
        """"Check the products available in order line and create new records in actual product quantity"""
        res = super(SaleOrder, self).create(vals)
        if vals['garment_sales']:
            if 'order_line' in vals:
                order_lines = vals['order_line']
                for line in order_lines:
                    self.env['actually.received.product.quantity'].create(
                        {'sale_order_id': res.id, 'product_id': line[2].get('product_id')})
        return res

    def write(self, values):
        # We are going to check add new product and remove product form order line
        if self.garment_sales:
            order_id = self.id
            if 'order_line' in values:
                lines = values['order_line']
                for line in lines:
                    if line[0] == 0:
                        # check product duplicate
                        duplicate_product_record = self.env['actually.received.product.quantity'].search([
                            ('sale_order_id', '=', order_id),
                            ('product_id', '=', line[2].get('product_id'))
                        ])
                        if not duplicate_product_record:
                            self.env['actually.received.product.quantity'].create({
                                'sale_order_id': order_id,
                                'product_id': line[2].get('product_id')
                            })
                    if line[0] == 2:
                        line_object = self.env['sale.order.line'].browse(line[1])
                        product = line_object.product_id
                        record = self.env['actually.received.product.quantity'].search(
                            [('sale_order_id', '=', order_id),
                             ('product_id', '=', product.id)])
                        if record:
                            record.unlink()
        return super(SaleOrder, self).write(values)

    def action_confirm(self):
        """Change stage when sent Confirm Quotation"""
        if self.price_estimate:
            if self.price_estimate.opportunity_no:
                stage = self.env['crm.stage'].search([('name', '=', 'Quotation Approved')])
                self.price_estimate.opportunity_no.write({'stage_id': stage.id})
        return super(SaleOrder, self).action_confirm()

    # @api.depends('picking_ids')
    # def _compute_picking_ids(self):
    #     for order in self:
    #         stock_picking = self.env['stock.picking'].search([
    #             ('sale_id', '=', self.id),
    #             ('garment_receipt', '!=', True)]).ids
    #         order.delivery_count = len(stock_picking)


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    @api.onchange('product_id')
    def _product_domain(self):
        """Filter Products based on Product template"""
        if self.order_id.garment_sales:
            garment_products = self.env['product.product'].search([('is_garment', '=', True)])
            return {
                'domain': {'product_id': [('id', 'in', garment_products.ids)]}
            }
        else:
            garment_products = self.env['product.product'].search([('is_garment', '=', False)])
            return {
                'domain': {'product_id': [('id', 'in', garment_products.ids)]}
            }


class ActuallyReceivedProductQuantity(models.Model):
    _name = "actually.received.product.quantity"
    _description = "Actually Received Product Quantity"

    product_id = fields.Many2one(comodel_name="product.product", string="Product")
    actually_received = fields.Float(string="Actually Received qty")
    sale_order_id = fields.Many2one(comodel_name="sale.order", string="Sale order ID")


class DeliveryRequirement(models.Model):
    _name = "delivery.requirement"
    _rec_name = "expected_delivery_date"

    # UCWP|FUN|-008 - Add Delivery Requirement tab
    expected_delivery_date = fields.Date(string="Expected Delivery Date")
    expected_quantity = fields.Integer(string="Expected Quantity")
    delivery_requirement_sale_order_id = fields.Many2one(comodel_name="sale.order", string="Sale order ID")
    product_id = fields.Many2one(comodel_name="product.product", string="Product")

    @api.onchange('product_id')
    def _domain_product(self):
        if self.delivery_requirement_sale_order_id.order_line:
            product_ids = []
            for line in self.delivery_requirement_sale_order_id.order_line:
                if line.product_id.id not in product_ids:
                    product_ids.append(line.product_id.id)
            return {
                'domain': {'product_id': [('id', 'in', product_ids)]}
            }
