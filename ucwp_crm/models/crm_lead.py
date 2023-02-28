from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from datetime import datetime, timedelta


class Lead(models.Model):
    _inherit = "crm.lead"
    _rec_name = "sequence_number"

    delivery_count = fields.Integer(string="Delivery Count", compute="_get_delivery_count")
    price_estimate_count = fields.Integer(string="Price Estimate Count", compute="_get_price_estimate_count")

    # Fields for Opportunity creation form
    product_id = fields.Many2one(comodel_name="product.template", string="Style")
    item = fields.Many2one(comodel_name="garment.type", string="Item")
    estimate_price = fields.Float(string="Estimated Price")
    order_qty = fields.Integer(string="Order Quantity")
    weight = fields.Float(string="Weight of Garment")
    wash_type = fields.Many2one(comodel_name="price.estimate.wash.type", string="Wash Type")
    buyer = fields.Many2one(comodel_name="res.partner", string="Buyer", store=True)
    contact_person = fields.Many2one(comodel_name="res.partner", string="Contact Person", store=True)

    sequence_number = fields.Char(string="Opportunity Number")

    @api.model
    def create(self, vals):
        """Set sequence"""
        sequence = self.env['ir.sequence'].next_by_code('opportunity.sequence.number') or _('New')
        vals['sequence_number'] = sequence
        return super(Lead, self).create(vals)

    def _get_delivery_count(self):
        # is_installed = self.env['ir.module.module'].search([('name', '=', 'union_colombo_washing_plant')])
        delivery_order = self.env['stock.picking.type'].search([('code', '=', 'outgoing')], limit=1)
        if self.partner_id:
            delivery_records = self.env['stock.picking'].search([
                ('picking_type_id', '=', delivery_order.id), ('state', '=', 'done'),
                ('partner_id', '=', self.partner_id.id)])
            sample_id = self.env.ref('ucwp_stock.product_category_sample')
            sample_sub_ids = self.env['product.category'].search([('parent_id', '=', sample_id.id)])
            if delivery_records:
                delivery_count = 0
                for delivery_record in delivery_records:
                    for move in delivery_record.move_ids_without_package:
                        if move.product_id:
                            if move.product_id.categ_id == sample_id or move.product_id.categ_id in sample_sub_ids:
                                delivery_count += 1
                                break
                self.delivery_count = delivery_count
            else:
                self.delivery_count = 0
        else:
            self.delivery_count = 0

    def action_view_delivery(self):
        delivery_order = self.env['stock.picking.type'].search([('code', '=', 'outgoing')], limit=1)
        if self.partner_id:
            delivery_records = self.env['stock.picking'].search([
                ('picking_type_id', '=', delivery_order.id), ('state', '=', 'done'),
                ('partner_id', '=', self.partner_id.id)])
            sample_id = self.env.ref('ucwp_stock.product_category_sample')
            sample_sub_ids = self.env['product.category'].search([('parent_id', '=', sample_id.id)])
            delivery_count = 0
            delivery_ids = []
            if delivery_records:
                for delivery_record in delivery_records:
                    for move in delivery_record.move_ids_without_package:
                        if move.product_id:
                            if move.product_id.categ_id == sample_id or move.product_id.categ_id in sample_sub_ids:
                                delivery_count += 1
                                delivery_ids.append(delivery_record.id)
                                break

            if delivery_count > 1:
                form_view = self.env.ref('stock.view_picking_form').id
                tree_view = self.env.ref('stock.vpicktree').id
                return {
                    'name': 'Garment Receipts',
                    'res_model': 'stock.picking',
                    'type': 'ir.actions.act_window',
                    'view_mode': 'list,form',
                    'views': [[tree_view, 'list'], [form_view, 'form']],
                    'target': 'current',
                    'domain': [('id', 'in', delivery_ids)],
                }
            elif delivery_count == 1:
                form_view = self.env.ref('stock.view_picking_form').id
                return {
                    'res_model': 'stock.picking',
                    'type': 'ir.actions.act_window',
                    'view_mode': 'form',
                    'view_id': form_view,
                    'res_id': delivery_ids[0],
                    'target': 'current',
                }
        else:
            raise UserError(_("Customer cannot be empty"))

    def _get_price_estimate_count(self):
        # is_price_estimate_installed = self.pool.get('ir.module.module').search(
        #     [('state', '=', 'installed'), ('name', '=', 'price_estimate')])  # check module installed or not
        if self.partner_id.id:
            price_estimate_record = self.env['pre.costing'].search([('customer', '=', self.partner_id.id)])
            if price_estimate_record:
                self.price_estimate_count = len(price_estimate_record)
            else:
                self.price_estimate_count = 0
        else:
            self.price_estimate_count = 0

    def action_view_price_estimates(self):
        if self.partner_id.id:
            price_estimate_record = self.env['pre.costing'].search([('customer', '=', self.partner_id.id)])
            if price_estimate_record:
                if len(price_estimate_record) > 1:
                    tree_view = self.env.ref('price_estimate.pre_costing_tree_view').id
                    form_view = self.env.ref('price_estimate.pre_costing_form_view').id
                    return {
                        'name': 'Price Estimate',
                        'res_model': 'pre.costing',
                        'type': 'ir.actions.act_window',
                        'view_mode': 'list,form',
                        'views': [[tree_view, 'list'], [form_view, 'form']],
                        'target': 'current',
                        'domain': [('id', 'in', price_estimate_record.ids)],
                    }
                if len(price_estimate_record) == 1:
                    form_view = self.env.ref('price_estimate.pre_costing_form_view').id
                    return {
                        'res_model': 'pre.costing',
                        'type': 'ir.actions.act_window',
                        'view_mode': 'form',
                        'view_id': form_view,
                        'res_id': price_estimate_record.id,
                        'target': 'current',
                    }


class PreCosting(models.Model):
    _inherit = "pre.costing"

    opportunity_no = fields.Many2one(comodel_name="crm.lead", string="Opportunity")

    @api.onchange('opportunity_no')
    def _onchange_opportunity(self):
        if not self.customer:
            self.customer = self.opportunity_no.partner_id
        if not self.buyer:
            self.buyer = self.opportunity_no.buyer
        if not self.product_id:
            self.product_id = self.opportunity_no.product_id
        if not self.order_qty:
            self.order_qty = self.opportunity_no.order_qty
        if not self.weight:
            self.weight = self.opportunity_no.weight
        if not self.wash_type:
            self.wash_type = self.opportunity_no.wash_type