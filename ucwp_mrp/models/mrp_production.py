from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from datetime import datetime
import pytz
from lxml import etree
import simplejson


class MrpProduction(models.Model):
    _inherit = "mrp.production"

    unique_no = fields.Many2one(comodel_name="mrp.no", string="Manufacture No.")
    product_color = fields.Char(string="Color")

    garment_allocation_line = fields.One2many(comodel_name="garment.allocation", inverse_name="mo_id",
                                              string="Garment Allocation")
    all_workorders_finished = fields.Boolean(string="Workorders Done", default=False)

    def finish_all_workorder(self):
        if self.workorder_ids:
            for workorder_id in self.workorder_ids:
                workorder_id.button_start()  # start button
                # Set duration
                workorder_id.duration = workorder_id.duration_expected
                workorder_id.button_finish()  # finish button
                # for component
                # for move_id in self.move_raw_ids:
                #     if move_id.workorder_id:
                #         if move_id.workorder_id.id == workorder_id.id:
                #             workorder_id.action_next()  # validate from tablet view
        if self.move_raw_ids:
            for move_id in self.move_raw_ids:
                to_consume = move_id.product_uom_qty
                reserved = move_id.reserved_availability
                consumed = 0
                if move_id.move_line_ids:
                    for move_line_id in move_id.move_line_ids:
                        move_line_id.qty_done = reserved
                        consumed += reserved

        self.all_workorders_finished = True

    def write(self, values):
        if 'state' in values:
            if values['state'] == 'confirmed':
                # Quantity validation with garment allocation total
                if self.garment_allocation_line:
                    total_line_qty = 0
                    for line in self.garment_allocation_line:
                        total_line_qty += line.lot_qty
                    if total_line_qty != self.product_qty:
                        raise UserError(
                            _("Total Quantity of garment allocation must be equal to Manufacture order quantity"))
                    # Inventory adjustments for selected lots in garment allocation
                    for garment_allocation_line in self.garment_allocation_line:

                        # If the selected lot is from grn (g/split) negative inventory location = Logistics
                        # if is from previous MO negative inventory location = post-production
                        post_production_loc = self.env['stock.location'].search([('name', '=', 'Post-Production'), (
                            'company_id', '=', self.env.context['allowed_company_ids'][0])])
                        location_id = post_production_loc
                        if 'G/SPLIT/' in garment_allocation_line.lot_id.display_name:
                            chem_categ_id = self.env.ref('ucwp_stock.product_category_chemical').id
                            # bulk_categ_id = self.env.ref('ucwp_stock.product_category_bulk').id
                            sample_categ_id = self.env.ref('ucwp_stock.product_category_sample').id
                            dev_sample_categ_id = self.env.ref('ucwp_stock.development_sample').id
                            prod_sample_categ_id = self.env.ref('ucwp_stock.production_sample').id
                            location_id = self.env['stock.location'].search([('name', '=', 'Logistics')])
                            if self.product_id.categ_id.id in [sample_categ_id, dev_sample_categ_id,
                                                               prod_sample_categ_id]:
                                location_id = self.env['stock.location'].search([('name', '=', 'Sample Room')])

                        available_record = self.env['stock.quant'].search([('product_id', '=', self.product_id.id),
                                                                           ('lot_id', '=',
                                                                            garment_allocation_line.lot_id.id),
                                                                           ('location_id', '=', location_id.id)])
                        if available_record:
                            new_lot_qty = -garment_allocation_line.lot_qty
                            self.env['stock.quant']._update_available_quantity(self.product_id, location_id,
                                                                               new_lot_qty,
                                                                               lot_id=garment_allocation_line.lot_id)
                        else:
                            raise ValidationError(_(garment_allocation_line.lot_id.display_name + "don't have "))
                else:
                    raise ValidationError(
                        _("Select a lot number for this manufacture order.\nUse \"Garment Allocation\" tab to select a lot number"))

        return super(MrpProduction, self).write(values)

    @api.onchange('bom_id', 'product_id')
    def _set_workorder_lines(self):
        if self.bom_id:
            bom_operation_line = 0
            for workorder_id in self.workorder_ids:
                workorder_id.temp = self.bom_id.operation_ids[bom_operation_line].temp
                workorder_id.ph_value = self.bom_id.operation_ids[bom_operation_line].ph_value
                bom_operation_line += 1

    @api.onchange('product_id')
    def _get_color(self):
        """Get color of product variant"""
        if self.product_id:
            variant_name = self.product_id.display_name
            self.product_color = variant_name.replace(self.product_id.product_tmpl_id.display_name, '').replace('(',
                                                                                                                '').replace(
                ')', '').replace(' ', '')


class MrpWorkorder(models.Model):
    _inherit = "mrp.workorder"

    ph_value = fields.Char(string="Ph")
    temp = fields.Float(string="Temp(℃)")
    instruction = fields.Many2one(comodel_name="instructions", string="Instruction")


class MrpRoutingWorkcenter(models.Model):
    _inherit = 'mrp.routing.workcenter'

    ph_value = fields.Char(string="Ph")
    temp = fields.Float(string="Temp(℃)")
    instruction = fields.Many2one(comodel_name="instructions", string="Instruction")


class MrpProductionWizard(models.TransientModel):
    _name = "mrp.production.wizard"

    product_id = fields.Many2one(comodel_name="product.product", string="Product")
    unique_no = fields.Many2one(comodel_name="mrp.no", string="Manufacture No.")


class ManufactureName(models.Model):
    _name = "mrp.no"

    name = fields.Char(string="Manufacture No.")


class MrpBom(models.Model):
    _inherit = 'mrp.bom'

    name = fields.Char(string="Bills of Materials Number", default="New")
    state = fields.Selection([('draft', 'Draft'), ('confirm', 'Confirm')], string="Status", default="draft")

    wash_type = fields.Many2one(comodel_name="wash.type", string="Wash Type")
    fabric = fields.Many2one(comodel_name="fabric.type", string="Fabric")
    remark = fields.Char(string="Remark")
    load_weight = fields.Float(string="Load Weight(kg)", digits=(5, 3))
    piece_weight = fields.Float(string="Piece Weight(g)")

    hydro_extract_time = fields.Float(string="Hydro Extractor (Minutes)")
    hot_dryer_temp = fields.Float(string="Hot Dryer Temp (°C)")
    hot_dryer_time = fields.Float(string="Hot Dryer Time (Minutes)")
    cool_dry = fields.Selection([('yes', 'Yes'), ('no', 'No')], string="Cool Dry")
    cool_dry_time = fields.Float(string="Cool Dry Time (Minutes)")

    prepared_by = fields.Many2one(comodel_name="res.users", string="Prepared by", readonly=True, tracking=True)
    date_approved = fields.Datetime(string="Date Approved", readonly=True, tracking=True)
    approved_by = fields.Many2one(comodel_name="res.users", string="Approved by", readonly=True, tracking=True)
    prepared_datetime = fields.Datetime(string="Date", readonly=True, tracking=True)

    product_color = fields.Char(string="Color")

    @api.onchange('product_id')
    def _get_color(self):
        """Get color of product variant"""
        if self.product_id:
            variant_name = self.product_id.display_name
            self.product_color = variant_name.replace(self.product_id.product_tmpl_id.display_name, '').replace('(',
                                                                                                                '').replace(
                ')', '').replace(' ', '')

    def name_get(self):
        return [(bom.id,
                 '%s%s%s' % (bom.name + ": ", bom.code and '%s: ' % bom.code or '', bom.product_tmpl_id.display_name))
                for bom in self]

    def _get_datetime(self):
        tz = pytz.timezone(self.env.user.tz)
        utc_time = datetime.utcnow()
        return datetime.strftime(utc_time, "%Y-%m-%d %H:%M:%S")

    @api.model
    def create(self, vals):
        """Set sequence for BoM"""
        sequence = self.env['ir.sequence'].next_by_code('bom.code') or _('New')
        vals['name'] = sequence

        """Set user for prepared by field when the user create BoM"""
        vals['prepared_by'] = self.env.user.id
        vals['prepared_datetime'] = self._get_datetime()

        return super(MrpBom, self).create(vals)

    def write(self, values):
        values['prepared_by'] = self.env.user.id
        values['prepared_datetime'] = self._get_datetime()
        return super(MrpBom, self).write(values)

    def action_confirm(self):
        self.write({'state': 'confirm', 'date_approved': self._get_datetime(), 'approved_by': self.env.user.id})

    def action_draft(self):
        self.write({'state': 'draft', 'date_approved': False, 'approved_by': False})

    @api.model
    def fields_view_get(self, view_id=None, view_type=False, toolbar=False, submenu=False):
        res = super(MrpBom, self).fields_view_get(view_id=view_id, view_type=view_type, toolbar=toolbar,
                                                  submenu=submenu)
        doc = etree.XML(res['arch'])
        if view_type == 'form':
            for node in doc.xpath("//field"):
                modifiers = simplejson.loads(node.get("modifiers"))
                if 'readonly' not in modifiers:
                    modifiers['readonly'] = [['state', '=', 'confirm']]
                else:
                    if type(modifiers['readonly']) != bool:
                        modifiers['readonly'].insert(0, '|')
                        modifiers['readonly'] += [['state', '=', 'confirm']]
                node.set('modifiers', simplejson.dumps(modifiers))
                res['arch'] = etree.tostring(doc)
        return res

    @api.onchange('piece_weight', 'product_qty')
    def _set_load_weight(self):
        self.load_weight = (self.piece_weight * self.product_qty) / 1000


class WashType(models.Model):
    _name = "wash.type"

    name = fields.Char(string="Wash Type")


class FabricType(models.Model):
    _name = "fabric.type"
    _description = "Fabric Type"

    name = fields.Char(string="Name")


class GarmentAllocation(models.Model):
    _name = "garment.allocation"

    # mo_barcode = fields.Many2one(comodel_name="stock.production.lot", string="Barcode", readonly=False)
    lot_id = fields.Many2one(comodel_name="stock.production.lot", string="Lot/Serial Number")
    lot_qty = fields.Float(string="Quantity")

    logistic_qty = fields.Float(string="Logistic Quantity", readonly=True)
    post_production_qty = fields.Float(string="Post Production Quantity", readonly=True)
    sample_room_qty = fields.Float(string="Sample Room Quantity", readonly=True)

    mo_id = fields.Many2one(comodel_name="mrp.production", string="MO ID")

    @api.onchange('lot_id')
    def _lot_id_domain(self):
        if self.lot_id:
            sample_categ_id = self.env.ref('ucwp_stock.product_category_sample').id
            dev_sample_categ_id = self.env.ref('ucwp_stock.development_sample').id
            prod_sample_categ_id = self.env.ref('ucwp_stock.production_sample').id

            location_id = self.env['stock.location'].search([('name', '=', 'Post-Production')])
            location = "Post-Production"
            if self.mo_id.product_id.categ_id.id in [sample_categ_id, dev_sample_categ_id, prod_sample_categ_id]:
                location_id = self.env['stock.location'].search([('name', '=', 'Sample Room')])
                location = "Sample Room"
            elif 'G/SPLIT/' in self.lot_id.display_name:
                location_id = self.env['stock.location'].search([('name', '=', 'Logistics')])
                location = "Logistics"

            available_record = self.env['stock.quant'].search([('product_id', '=', self.mo_id.product_id.id),
                                                               ('lot_id', '=', self.lot_id.id),
                                                               ('location_id', '=', location_id.id),
                                                               ('quantity', '>', 0)])
            if location == "Logistics":
                self.logistic_qty = available_record.quantity
                self.post_production_qty = 0
            if location == "Post-Production":
                self.post_production_qty = available_record.quantity
                self.logistic_qty = 0
            if location == "Sample Room":
                self.sample_room_qty = available_record.quantity

        else:
            lot_ids = self.env['stock.production.lot'].search(
                [('product_id', '=', self.mo_id.product_id.id)], order="create_date desc")
            # [('product_id', '=', self.mo_id.product_id.id), ('product_type', '=', 'material')])
            available_lots = []
            for lot_id in lot_ids:
                if lot_id:
                    stock_record = self.env['stock.quant'].search([('lot_id', '=', lot_id.id)])
                    for record in stock_record:
                        if record.location_id.name in ["Logistics", "Post-Production",
                                                       "Sample Room"] and record.quantity > 0 and lot_id.id not in available_lots:
                            available_lots.append(lot_id.id)

            return {
                'domain': {'lot_id': [('id', 'in', available_lots)]}
            }

    @api.onchange('lot_qty')
    def _lot_qty_validation(self):
        if self.lot_id:
            chem_categ_id = self.env.ref('ucwp_stock.product_category_chemical').id
            # bulk_categ_id = self.env.ref('ucwp_stock.product_category_bulk').id
            sample_categ_id = self.env.ref('ucwp_stock.product_category_sample').id
            dev_sample_categ_id = self.env.ref('ucwp_stock.development_sample').id
            prod_sample_categ_id = self.env.ref('ucwp_stock.production_sample').id
            location_id = self.env['stock.location'].search([('name', '=', 'Post-Production')])
            if self.mo_id.product_id.categ_id.id in [sample_categ_id, dev_sample_categ_id, prod_sample_categ_id]:
                location_id = self.env['stock.location'].search([('name', '=', 'Sample Room')])
            elif 'G/SPLIT/' in self.lot_id.display_name:
                location_id = self.env['stock.location'].search([('name', '=', 'Logistics')])

            available_record = self.env['stock.quant'].search([('product_id', '=', self.mo_id.product_id.id),
                                                               ('lot_id', '=', self.lot_id.id),
                                                               ('location_id', '=', location_id.id),
                                                               ('quantity', '>', 0)])
            if available_record and self.lot_qty > available_record.quantity:
                raise ValidationError(_(self.lot_id.display_name + " have only " + str(available_record.quantity)))


class Instructions(models.Model):
    _name = "instructions"

    name = fields.Char(string="Instruction")
