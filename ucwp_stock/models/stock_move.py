import datetime

from odoo import api, fields, models, _

from odoo.exceptions import UserError, ValidationError

from collections import defaultdict


class Picking(models.Model):
    _inherit = "stock.picking"

    # Washing Contract
    sale_id = fields.Many2one(comodel_name="sale.order", string="Washing Contract", domain="[('state', '=', 'sale')]")

    # Gate pass number
    customer_gate_pass_no = fields.Char(string="Customer Gate Pass")
    customer_manual_ref = fields.Char(string="Manual Ref")

    vehicle_number = fields.Char(string='Vehicle Number')

    grn_type = fields.Boolean(string="Garment GRN", default=True)

    @api.onchange('sale_id')
    def set_moves(self):
        if self.sale_id and not self.move_ids_without_package:
            sid = self.sale_id
            order_lines = []
            for line in self.sale_id.order_line:
                record = (0, 0, {'company_id': self.env.company.id, 'location_dest_id': self.location_dest_id.id,
                                 'location_id': self.location_id.id, 'display_name': line.display_name,
                                 'name': line.name,
                                 'po_availability': 'po' if line.po_no else False,
                                 'customer_ref': line.po_no.id if line.po_no else False,
                                 'picking_id': self.id, 'picking_type_id': self.picking_type_id.id,
                                 'state': self.state, 'product_id': line.product_id.id,
                                 'product_packaging_id': line.product_packaging_id.id,
                                 'product_qty': line.product_uom_qty, 'product_tmpl_id': line.product_template_id.id,
                                 'product_type': line.product_type, 'product_uom': line.product_uom.id,
                                 'product_uom_category_id': line.product_uom_category_id.id,
                                 'product_uom_qty': line.product_uom_qty})
                order_lines.append(record)
            self.move_ids_without_package = order_lines
            self.sale_id = sid


class StockMove(models.Model):
    _inherit = "stock.move"

    wash_type = fields.Selection([('wash', 'Wash'), ('rewash', 'Re-wash')], string="Wash Type")
    comment = fields.Text(string="Comment")
    done_qty = fields.Float(string="Total Done")
    fault_type = fields.Selection([('customer_fault', "Customer Fault"), ('uc_fault', 'UC Fault')],
                                  string="Fault")
    # GRN Operation Type
    is_garment = fields.Boolean(string="Is Garment")
    is_chemical = fields.Boolean(string="Is Chemical")

    # PO availability
    po_availability = fields.Selection([('po', 'PO'), ('temp_po', 'TEMP PO'), ('no_po', 'No PO')],
                                       string='PO Availability')
    customer_ref = fields.Many2one(comodel_name="po.number", string='Customer PO Ref')
    responsible_person = fields.Many2one(comodel_name="res.users", string="Responsible Person")

    @api.onchange('product_id')
    def _product_domain(self):
        chem_categ_id = self.env.ref('ucwp_stock.product_category_chemical').id
        bulk_categ_id = self.env.ref('ucwp_stock.product_category_bulk').id
        sample_categ_id = self.env.ref('ucwp_stock.product_category_sample').id
        accessory_categ_id = self.env.ref('ucwp_stock.product_category_accessory').id
        dev_sample_categ_id = self.env.ref('ucwp_stock.development_sample').id
        prod_sample_categ_id = self.env.ref('ucwp_stock.production_sample').id
        products = self.env['product.product'].search([('active', '=', True)])
        chem_products = []
        garment_product = []
        for product in products:
            if product.product_tmpl_id.categ_id.id == chem_categ_id:
                chem_products.append(product.id)
            if product.product_tmpl_id.categ_id.id in [bulk_categ_id, sample_categ_id, accessory_categ_id,
                                                       dev_sample_categ_id, prod_sample_categ_id]:
                garment_product.append(product.id)
        if self.picking_id.grn_type:
            return {
                'domain': {'product_id': [('id', 'in', garment_product)]}
            }
        else:
            return {
                'domain': {'product_id': [('id', 'in', chem_products)]}
            }


class StockMoveWizard(models.TransientModel):
    _name = "stock.move.wizard"

    message = fields.Char(string="Message")


class StockMoveLine(models.Model):
    _inherit = "stock.move.line"

    barcode = fields.Char(string="Barcode", readonly=True)

    # GRN Operation Type
    is_garment = fields.Boolean(string="Is Garment", related="move_id.is_garment", store=True)
    is_chemical = fields.Boolean(string="Is Chemical", related="move_id.is_chemical", store=True)

    @api.model
    def create(self, vals):
        if 'picking_id' in vals:
            picking_obj = self.env['stock.picking'].browse(vals.get('picking_id'))
            if 'qty_done' in vals and picking_obj.picking_type_code == "incoming":
                stock_move = self.env['stock.move'].browse(vals.get('move_id'))
                if stock_move:
                    product_id = stock_move.product_id.id
                else:
                    product_id = vals['product_id']
                sequence = self.env['ir.sequence'].next_by_code('stock.move.line') or _('New')
                lot_id = self.env['stock.production.lot'].create({
                    'name': sequence,
                    'product_id': product_id,
                    'barcode': sequence,
                    'product_type': 'material',
                    'company_id': self.env.company.id
                })
                if lot_id:
                    vals['lot_id'] = lot_id.id
                    vals['barcode'] = lot_id.name

                # # create log note for lot creation
                # self.env['lot.trace.line'].sudo().create({
                #     'lot_id': lot_id.id,
                #     'log_date': datetime.datetime.now(),
                #     'log_type': 'created',
                #     'user': self.env.user.id,
                #     'create_method': 'receipt',
                #     'receipt_id': picking_obj.id,
                #     'reference': picking_obj.name,
                # })
        return super(StockMoveLine, self).create(vals)

    @api.onchange('product_id')
    def _onchange_product_filter(self):
        if self.picking_id.picking_type_code == 'incoming':
            chem_categ_id = self.env.ref('ucwp_stock.product_category_chemical').id
            bulk_categ_id = self.env.ref('ucwp_stock.product_category_bulk').id
            sample_categ_id = self.env.ref('ucwp_stock.product_category_sample').id
            accessory_categ_id = self.env.ref('ucwp_stock.product_category_accessory').id
            dev_sample_categ_id = self.env.ref('ucwp_stock.development_sample').id
            prod_sample_categ_id = self.env.ref('ucwp_stock.production_sample').id
            products = self.env['product.product'].search([('active', '=', True)])
            chem_products = []
            garment_product = []
            for product in products:
                if product.product_tmpl_id.categ_id.id == chem_categ_id:
                    chem_products.append(product.id)
                if product.product_tmpl_id.categ_id.id in [bulk_categ_id, sample_categ_id, accessory_categ_id,
                                                           dev_sample_categ_id, prod_sample_categ_id]:
                    garment_product.append(product.id)
            if self.picking_id.grn_type:
                return {
                    'domain': {'product_id': [('id', 'in', garment_product)]}
                }
            else:
                return {
                    'domain': {'product_id': [('id', 'in', chem_products)]}
                }

    def print_barcode(self):
        """ Print barcode on PDF """
        data = {
            'barcode': self.barcode,
        }
        return self.env.ref('ucwp_stock.stock_move_line_barcode_action').report_action(self, data=data)

    # @api.onchange('qty_done')
    # def _validate_done_qty(self):
    #     if self.picking_id.picking_type_code in ['internal',
    #                                              'outgoing'] and self.picking_id.immediate_transfer is not True:
    #         if self.qty_done > self.product_uom_qty:
    #             raise ValidationError(_("Done quantity cannot be larger than reserved quantity"))


class ProductionLot(models.Model):
    _inherit = 'stock.production.lot'

    barcode = fields.Char(string="Barcode", readonly=True, compute="_compute_barcode")
    product_type = fields.Selection([('material', 'Material'), ('finish', 'Finish Product')], string='Product Type')

    def _compute_barcode(self):
        self.barcode = self.name
