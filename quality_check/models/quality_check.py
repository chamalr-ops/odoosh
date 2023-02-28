from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError

from lxml import etree
import simplejson  # If not installed, you have to install it by executing pip install simplejson


class QualityCheckBasic(models.Model):
    _name = "quality.check.basic"
    _description = 'Quality Check'
    _inherit = ['mail.thread']
    _rec_name = "name"

    # [UC-11]
    name = fields.Char(string="Quality Check Number", default="New")
    partner_id = fields.Many2one(comodel_name='res.partner', string='Customer')
    grn = fields.Many2one(comodel_name="stock.picking", string="GRN")
    quality_check_lines = fields.One2many(comodel_name="quality.check.lines", inverse_name="quality_check_id",
                                          string="Quality Lines")
    quality_point = fields.Selection([('before_wash', 'Before Wash'), ('after_wash', 'After Wash')],
                                     string="Quality Point")
    manufacture_order = fields.Many2one(comodel_name="mrp.production", string="Manufacture Orders")
    state = fields.Selection([('draft', 'Draft'), ('lock', 'Lock')], string='State', default='draft', readonly=True)

    @api.onchange('grn')
    def _domain_filter_grn(self):
        receipt = self.env['stock.picking.type'].search(
            [('company_id', '=', self.env.company.id), ('code', '=', 'incoming'),
             ('use_existing_lots', '=', False)], order="id desc", limit=1)
        receipt_records = self.env['stock.picking'].search(
            [('company_id', '=', self.env.company.id), ('picking_type_id', '=', receipt.id),
             ('state', '=', 'done')])
        return {
            'domain': {'grn': [('id', 'in', receipt_records.ids)]}
        }

    def set_to_draft(self):
        self.write({'state': 'draft'})

    def set_to_validate(self):
        check_products = self.quality_check_lines.product
        check_lines = self.quality_check_lines
        product_list = []
        product_names = []
        for product in check_products:
            total_inspect = 0
            total_process = 0
            for line in check_lines:
                if line.product.id == product.id:
                    total_inspect += line.inspected_qty
                    for line_info in line.quality_check_line_info:
                        total_process += line_info.quantity
            if total_inspect != total_process:
                product_list.append(product.id)
                product_names.append(product.name)
        if len(product_list) > 0:
            products = ' '.join([str(name) + ',' for name in product_names])
            error = "Product" + " - " + products + " Total of Pass/Fail quantity must not be less than the Inspected Quantity "
            raise ValidationError(error)
        else:
            self.write({'state': 'lock'})

    # Generate a Sequence for Quality Check
    @api.model
    def create(self, values):
        qc_sequence = self.env['ir.sequence'].next_by_code('quality.check.number') or _('New')
        values['name'] = qc_sequence
        return super(QualityCheckBasic, self).create(values)

    def action_send_quality_email(self):
        ir_model_data = self.env['ir.model.data']
        try:
            template_id = ir_model_data._xmlid_lookup('quality_check.quality_check_report_email_template')[2]
        except ValueError:
            template_id = False

        try:
            compose_form_id = ir_model_data._xmlid_lookup('mail.email_compose_message_wizard_form')[2]
        except ValueError:
            compose_form_id = False
        ctx = dict(self.env.context or {})
        ctx.update({
            'default_model': 'quality.check.basic',
            'active_model': 'quality.check.basic',
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
        ctx['model_description'] = _('Quality Check Report')

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

    @api.model
    def fields_view_get(self, view_id=None, view_type=False, toolbar=False, submenu=False):
        res = super(QualityCheckBasic, self).fields_view_get(view_id=view_id, view_type=view_type, toolbar=toolbar,
                                                             submenu=submenu)
        doc = etree.XML(res['arch'])
        if view_type == 'form':
            for node in doc.xpath("//field"):
                modifiers = simplejson.loads(node.get("modifiers"))
                if 'readonly' not in modifiers:
                    modifiers['readonly'] = [['state', '=', 'lock']]
                else:
                    if type(modifiers['readonly']) != bool:
                        modifiers['readonly'].insert(0, '|')
                        modifiers['readonly'] += [['state', '=', 'lock']]
                node.set('modifiers', simplejson.dumps(modifiers))
                res['arch'] = etree.tostring(doc)
        return res

    # def write(self, vals):
    #     if self.quality_point == 'after_wash' and self.manufacture_order:
    #         pass
    #
    #     return super(QualityCheckBasic, self).write(vals)


class QualityCheckLines(models.Model):
    _name = "quality.check.lines"
    _description = "Quality Check Lines"

    product = fields.Many2one(comodel_name="product.product", string="Product")
    lot_no = fields.Many2one(comodel_name="stock.production.lot", string="Lot No", required=True)
    quality_check_id = fields.Many2one(comodel_name="quality.check.basic", string="Quality Check")
    inspected_qty = fields.Float(string="To Inspect")
    quality_point = fields.Selection([('before_wash', 'Before Wash'), ('after_wash', 'After Wash')],
                                     string="Quality Point")
    quality_check_line_info = fields.One2many(comodel_name="quality.check.line.info",
                                              inverse_name="quality_check_line_id", string="Quality Check Info")
    rest_qty = fields.Float(string="Rest Inspected qty", compute="_set_rest_inspected_qty")
    grn = fields.Many2one(comodel_name="stock.picking", string="GRN", related="quality_check_id.grn", store=True)
    partner_id = fields.Many2one(comodel_name="res.partner", string='Customer', related="quality_check_id.partner_id",
                                 store=True)
    lot_qty = fields.Float(string="Manufactured Quantity", readonly=True)
    grn_qty = fields.Float(string="Lot Quantity", readonly=True)

    # Set initial value to rest qty
    @api.depends('quality_check_line_info.quantity')
    def _set_rest_inspected_qty(self):
        for line in self:
            quantity_done = 0
            for quality_check_info_record in line.quality_check_line_info:
                quantity_done += quality_check_info_record.quantity
            line.rest_qty = quantity_done
            if line.quality_point == "after_wash":
                # finish_product_operation = self.env['stock.picking.type'].search(
                #     [('name', '=', 'Store Finished Product')],
                #     limit=1)
                # finish_lot = self.env['stock.quant'].search([('lot_id', '=', line.lot_no.id),
                #                                              ('location_id', '=',
                #                                               finish_product_operation.default_location_dest_id.id),
                #                                              ('product_id', '=', line.product.id)])

                # line.lot_no = self.quality_check_id.manufacture_order.lot_producing_id
                line.lot_qty = self.quality_check_id.manufacture_order.qty_producing
                # this or search from quality check location
                if quantity_done > self.quality_check_id.manufacture_order.product_qty:
                    raise ValidationError(_("Total of Pass/Fail quantities cannot exceed inspected quantity"))
            elif line.quality_point == 'before_wash':
                if quantity_done > line.inspected_qty:
                    raise ValidationError(_("Total of Pass/Fail quantities cannot exceed \"To Inspected Quantity\""))

    @api.onchange('product', 'lot_no')
    def update_domain(self):
        """Set demain to filter product and Lot No"""
        if self.quality_point == 'before_wash':
            product_ids = self.quality_check_id.grn.move_ids_without_package.product_id.ids
            split_lines = self.quality_check_id.grn.move_ids_without_package.move_line_nosuggest_ids
            if self.lot_no:
                self.grn_qty = self.lot_no.product_qty
            lot_name_list = []
            for split_line in split_lines:
                if split_line.product_id.id == self.product.id:
                    lot_name_list.append(split_line.lot_id.name)
            lot_ids = self.env['stock.production.lot'].search([('name', 'in', lot_name_list)])
            if lot_ids and product_ids:
                return {
                    'domain': {'lot_no': [('id', 'in', lot_ids.ids)], 'product': [('id', 'in', product_ids)]}
                }
            if not lot_ids and product_ids:
                return {
                    'domain': {'lot_no': [('id', '=', 0)], 'product': [('id', 'in', product_ids)]}
                }
        if self.quality_point == 'after_wash':
            product_id = self.quality_check_id.manufacture_order.product_id.id
            lot_id = self.quality_check_id.manufacture_order.lot_producing_id.id
            if self.lot_no:
                self.lot_qty = self.lot_no.product_qty
            return {
                'domain': {'product': [('id', '=', product_id)], 'lot_no': [('id', '=', lot_id)]}
            }

    @api.onchange('inspected_qty', 'lot_no')
    def _validate_inspected_qty(self):
        if self.inspected_qty and self.lot_no:
            if self.inspected_qty > self.lot_no.product_qty:
                raise ValidationError(_("Inspected quantity cannot be greater than product quantity of lot"))


class QualityCheckLineInfo(models.Model):
    _name = "quality.check.line.info"
    _description = "Quality Check line Information"

    pass_fail = fields.Selection([('pass', 'Pass'), ('fail', 'Fail')], string="Pass/Fail", required=True)
    quantity = fields.Float(string="Quantity", required=True)
    defects = fields.Many2many(comodel_name="defects", string="Defects")
    image = fields.Binary(string="Image")
    comment = fields.Char(string="Comment")
    state = fields.Selection([('processed', 'Process'), ('returned', 'Returned'),
                              ('rewashed', 'Rewash'), ('disposed', 'Disposed')], string="State", readonly=True)
    quality_check_line_id = fields.Many2one(comodel_name="quality.check.lines", string="Quality Check Line ID")
    quality_point = fields.Selection([('before_wash', 'Before Wash'), ('after_wash', 'After Wash')],
                                     string="Quality Point")

    # Map Returns and Return Count
    return_count = fields.Integer(string="Invoice Count", compute="_get_returns")
    return_id = fields.Many2one(comodel_name="stock.picking", string="Return ID", compute="_get_returns")

    grn = fields.Many2one(comodel_name="stock.picking", string="GRN", related="quality_check_line_id.grn", store=True)
    partner_id = fields.Many2one(comodel_name="res.partner", string="GRN",
                                 related="quality_check_line_id.partner_id", store=True)
    lot_id = fields.Many2one(comodel_name="stock.production.lot", string="Lot No")
    product_id = fields.Many2one(comodel_name='product.product', string="Product",
                                 related="quality_check_line_id.product", store=True)

    display_process_button = fields.Boolean(compute="_display_button")
    display_return_button = fields.Boolean(compute="_display_button")
    display_rewash_button = fields.Boolean(compute="_display_button")
    display_dispose_button = fields.Boolean(compute="_display_button")

    def _get_returns(self):
        returns = self.env['stock.picking'].search(
            [('quality_fail_line', '=', self.id), ('state', 'not in', ['cancel'])])
        if returns:
            self.return_count = 1
            self.return_id = returns.id
        else:
            self.return_count = 0

    @api.depends('quality_point', 'pass_fail')
    def _display_button(self):
        """ Set visibility for Buttons """
        for record in self:
            # Process button visibility
            if record.quality_point == 'before_wash' and record.pass_fail == 'fail':
                record.display_process_button = True
            elif record.quality_point == 'after_wash':
                record.display_process_button = True
            else:
                record.display_process_button = False

            # Dispose Button visibility
            if record.pass_fail == 'fail':
                record.display_dispose_button = True
            else:
                record.display_dispose_button = False

            # Rewash Button visibility
            if record.quality_point == 'after_wash' and record.pass_fail == 'fail':
                record.display_rewash_button = True
            else:
                record.display_rewash_button = False

            # Return Button visibility
            if record.quality_point == 'before_wash' and record.pass_fail == 'fail':
                record.display_return_button = True
            else:
                record.display_return_button = False

    def process_garment(self):
        """ Process garment: if before wash fail but need to process
                             and after wash pass garments """
        if not self.quality_check_line_id:
            raise UserError("Please save the complete Quality check record first ")
        if self.quality_point == 'before_wash' and self.pass_fail == 'fail':
            self.write({'state': 'processed'})
        if self.quality_point == 'after_wash' and self.pass_fail == 'pass':
            self.write({'state': 'processed'})
            view = self.env.ref('stock.view_picking_form')
            # internal_transfer_operation = self.env['stock.picking.type'].search(
            #     [('company_id', '=', self.env.company.id), ('code', '=', 'internal')], order='sequence ASC', limit=1)
            internal_transfer_operation = self.env['stock.picking.type'].search(
                [('name', '=', 'Process Garment'), ('sequence_code', '=', 'PG')])
            return {
                'res_model': 'stock.picking',
                'type': 'ir.actions.act_window',
                'view_mode': 'form',
                'view_id': view.id,
                'target': 'current',
                'context': {
                    'default_picking_type_id': internal_transfer_operation.id,
                    'default_immediate_transfer': True,
                    'default_move_line_ids_without_package': [
                        (0, 0, {'product_id': self.quality_check_line_id.product.id,
                                'location_id': internal_transfer_operation.default_location_src_id.id,
                                'location_dest_id': internal_transfer_operation.default_location_dest_id.id,
                                'lot_id': self.lot_id.id,
                                'product_uom_id': self.quality_check_line_id.product.uom_id.id,
                                'qty_done': self.quantity, })]
                },
            }

    def return_garment(self):
        """ Action for before and after wash garment returns """
        if not self.quality_check_line_id:
            raise UserError("Please save the complete Quality check record first ")
        self.write({'state': 'returned'})
        return_operation = self.env['stock.picking.type'].search(
            [('company_id', '=', self.env.company.id), ('code', '=', 'incoming'),
             ('use_create_lots', '=', False)], order="id desc", limit=1)
        view = self.env.ref('stock.view_picking_form')
        return {
            'res_model': 'stock.picking',
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'view_id': view.id,
            'target': 'current',
            'context': {
                'default_picking_type_id': return_operation.id,
                'default_location_id': self.grn.location_dest_id.id,
                'default_location_dest_id': self.grn.location_id.id,
                'default_partner_id': self.partner_id.id,
                'default_origin': self.grn.name,
                'default_bw_return_lot': self.lot_id.id,
                'default_immediate_transfer': True,
                'default_quality_fail_line': self.id,
                'default_move_ids_without_package': [
                    (0, 0, {'location_id': self.grn.location_dest_id.id,
                            'location_dest_id': self.grn.location_id.id,
                            'product_id': self.quality_check_line_id.product.id,
                            'name': self.quality_check_line_id.product.display_name,
                            'product_uom': self.quality_check_line_id.product.uom_id.id,
                            'product_uom_qty': self.quantity,
                            'bw_return_lot': self.lot_id.id})]
            }
        }

    def action_view_return(self):
        return_form_view = self.env.ref('stock.view_picking_form')
        record = self.env['stock.picking'].search(
            [('quality_fail_line', '=', self.id), ('state', 'not in', ['cancel'])], limit=1)
        return {
            'res_model': 'stock.picking',
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'view_id': return_form_view.id,
            'res_id': record.id,
            'target': 'current',
        }

    def rewash_garment(self):
        if not self.quality_check_line_id:
            raise UserError("Please save the complete Quality check record first ")
        self.write({'state': 'rewashed'})
        if self.pass_fail == 'fail' and self.quality_point == 'after_wash':
            view = self.env.ref('stock.view_picking_form')
            # internal_transfer_operation = self.env['stock.picking.type'].search(
            #     [('code', '=', 'internal'), ('use_create_lots', '=', False)])
            # internal_transfer = internal_transfer_operation[0]
            internal_transfer_operation = self.env['stock.picking.type'].search(
                [('name', '=', 'Rewash Garment'), ('sequence_code', '=', 'RG')])
            return {
                'res_model': 'stock.picking',
                'type': 'ir.actions.act_window',
                'view_mode': 'form',
                'view_id': view.id,
                'target': 'current',
                'context': {
                    'default_picking_type_id': internal_transfer_operation.id,
                    'default_immediate_transfer': True,
                    # 'default_move_line_ids_without_package': []
                    'default_move_line_ids_without_package': [
                        (0, 0, {'product_id': self.quality_check_line_id.product.id,
                                # 'name': self.quality_check_line_id.product.display_name,
                                'location_id': internal_transfer_operation.default_location_src_id.id,
                                'location_dest_id': internal_transfer_operation.default_location_dest_id.id,
                                'lot_id': self.lot_id.id,
                                'product_uom_id': self.quality_check_line_id.product.uom_id.id,
                                # 'product_uom_qty': self.quantity,
                                'qty_done': self.quantity, })]
                    # 'lot_id': self.quality_check_line_id.lot_no.id})]
                },
            }

    def dispose_garment(self):
        if not self.quality_check_line_id:
            raise UserError("Please save the complete Quality check record first ")
        self.write({'state': 'disposed'})
        view = self.env.ref('stock.view_picking_form')
        # internal_transfer_operation = self.env['stock.picking.type'].search(
        #     [('code', '=', 'internal'), ('name', '=', 'Internal Transfers')])
        internal_transfer_operation = self.env['stock.picking.type'].search(
                [('name', '=', 'Dispose Garment'), ('sequence_code', '=', 'DG')])
        return {
            'res_model': 'stock.picking',
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'view_id': view.id,
            'target': 'current',
            'context': {
                    'default_picking_type_id': internal_transfer_operation.id,
                    'default_immediate_transfer': True,
                    'default_move_line_ids_without_package': [
                        (0, 0, {'product_id': self.quality_check_line_id.product.id,
                                'location_id': internal_transfer_operation.default_location_src_id.id,
                                'location_dest_id': internal_transfer_operation.default_location_dest_id.id,
                                'lot_id': self.lot_id.id,
                                'product_uom_id': self.quality_check_line_id.product.uom_id.id,
                                'qty_done': self.quantity, })]
                },
        }


class DefectsLines(models.Model):
    _name = 'defects.lines'

    defect = fields.Many2one(comodel_name="defects", string="Defect", required=True)
    quantity = fields.Integer(string="Quantity", required=True)
    quality_check_id = fields.Many2one(comodel_name="quality.check", string="Quality Check Id")


class DefectRecordLines(models.Model):
    _name = "defects"

    name = fields.Char(string="Name")
    code = fields.Char(string="Code")
