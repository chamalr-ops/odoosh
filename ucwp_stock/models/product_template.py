from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from datetime import datetime, timedelta


class ProductTemplate(models.Model):
    _inherit = 'product.template'
    _order = 'create_date desc'

    is_garment = fields.Boolean(string="Is Garment Product ?", default=False, readonly=True)
    is_chemical = fields.Boolean(string='Is Chemical ?', default=False, readonly=True)

    # Price estimate
    price_estimate_count = fields.Integer(string="Price Estimate Count", compute="_get_price_estimate_count")

    # Enable tracking for name field
    name = fields.Char('Name', index=True, required=True, translate=True, tracking=True, track_visibility="onchange")

    # Add chemical standards to product template
    chemical_standards = fields.One2many(comodel_name="chemical.standards", inverse_name="product_tmpl_id",
                                         string="Chemical Standards")

    # Add certification to product template and product variant
    available_certification = fields.Boolean(string="Available Certification")
    certification = fields.Text(string="Certification")

    # Test/Lab Reports tab
    lab_reports = fields.One2many(comodel_name="lab.reports", inverse_name="product_template_id",
                                  string="Test/Lab Reports")

    # Set Active / Inactive to Product Template
    active = fields.Boolean(string="Active", default=True)

    garment_type = fields.Many2one(comodel_name="garment.type", string="Garment Type")
    customer = fields.Many2one(comodel_name="res.partner", string="Customer")
    buyer = fields.Many2one(comodel_name="res.partner", string="Buyer")

    # ++++++++++++++++++++++++++++++++++++++++++ UCWP|IMP|-00050 MSDS II tab +++++++++++++++++++++++++++++++++++++++++++
    other_name = fields.Many2one(comodel_name="other.name", string="Other Name")
    manufacturer_formulator = fields.Many2one(comodel_name="formulator", string="Manufacturer / Formulator(SDS)")
    chemical_formulator_type = fields.Many2one(comodel_name="chemical.formulator.type",
                                               string="Chemical Formulator Type")
    local_agent = fields.Many2one(comodel_name="res.partner", string="Local Agent")
    environment = fields.Selection([('low', 'Low'), ('medium', 'Medium'), ('high', 'High')], string="Environment")
    worker_health = fields.Selection([('low', 'Low'), ('medium', 'Medium'), ('high', 'High')], string="Worker Health")
    location = fields.Many2one(comodel_name="location", string="Location")
    category = fields.Many2one(comodel_name="chemical.category", string="Category")
    chemical_type = fields.Many2one(comodel_name="chemical.type", string="Chemical Type")
    used_for = fields.Many2one(comodel_name="chemical.used.for", string="Used for")
    available = fields.Boolean(string="Available")
    issue_date = fields.Date(string="Issue Date")
    version = fields.Float(string="Version")
    revision_date = fields.Date(string="Revision Date")
    explosive = fields.Boolean(string="Explosive")
    health_hazard = fields.Boolean(string="Health Hazard")
    flammable = fields.Boolean(string="Flammable")
    environmental_hazard = fields.Boolean(string="Environmental Hazard")
    toxic = fields.Boolean(string="Toxic")
    corrosive = fields.Boolean(string="Corrosive")
    oxidizing = fields.Boolean(string="Oxidizing")
    compressed_gas = fields.Boolean(string="Compressed Gas")
    warning_irritant = fields.Boolean(string="Warning/ Irritant")
    respirator = fields.Boolean(string="Respirator")
    gloves = fields.Boolean(string="Gloves")
    footwear = fields.Boolean(string="Foot Wear")
    eye_wear = fields.Boolean(string="Eye Wear")
    apron = fields.Boolean(string="Apron")
    dust_mask = fields.Boolean(string="Dust Mask")
    overalls = fields.Boolean(string="Overalls")
    face_shield = fields.Boolean(string="Face Shield")
    safety_helmet = fields.Boolean(string="Safety Helmet")
    measures_for_cleaning_english = fields.Text(string="Measures for Cleaning (English)")
    measures_for_cleaning_sinhala = fields.Text(string="Measures for Cleaning (Sinhala)")
    storage_condition_english = fields.Text(string="Storage Condition (English)")
    storage_condition_sinhala = fields.Text(string="Storage Condition (Sinhala)")
    hazard_identification_english = fields.Text(string="Hazard Identification (English)")
    hazard_identification_sinhala = fields.Text(string="Hazard Identification (Sinhala)")
    health = fields.Selection(
        [('not_available', 'N/A'), ('health0', '0'), ('health1', '1'), ('health2', '2'), ('health3', '3'),
         ('health4', '4'), ('health5', '5')], string="Health")
    flammability = fields.Selection(
        [('not_available', 'N/A'), ('flammability0', '0'), ('flammability1', '1'), ('flammability2', '2'),
         ('flammability3', '3'), ('flammability4', '4'), ('flammability5', '5')], string="Flammability")
    reactivity_level = fields.Selection(
        [('not_available', 'N/A'), ('reactivity0', '0'), ('reactivity1', '1'), ('reactivity2', '2'),
         ('reactivity3', '3'), ('reactivity4', '4'), ('reactivity5', '5')], string="Reactivity")
    contact = fields.Selection(
        [('not_available', 'N/A'), ('contact0', '0'), ('contact1', '1'), ('contact2', '2'),
         ('contact3', '3'), ('contact4', '4'), ('contact5', '5')], string="Contact")
    severity = fields.Selection(
        [('1', '1'), ('2', '2'),
         ('3', '3'), ('4', '4'), ('5', '5')], string="Severity")
    likelihood = fields.Selection(
        [('1', '1'), ('2', '2'),
         ('3', '3'), ('4', '4'), ('5', '5')], string="Likelihood")
    risk_rating = fields.Integer(string="Risk Rating")
    storage_class = fields.Many2one(comodel_name="storage.class", string="Storage Class")
    water = fields.Boolean(string="Water")
    foom = fields.Boolean(string="Foam")
    dry_powder = fields.Boolean(string="Dry Powder")
    carbon_dioxide = fields.Boolean(string="Carbon Dioxide")
    inhalation_english = fields.Text(string="Inhalation (English)")
    inhalation_sinhala = fields.Text(string="Inhalation (Sinhala)")
    eye_contact_english = fields.Text(string="Eye Contact (English)")
    eye_contact_sinhala = fields.Text(string="Eye Contact (Sinhala)")
    skin_contact_english = fields.Text(string="Skin Contact (English)")
    skin_contact_sinhala = fields.Text(string="Skin Contact (Sinhala)")
    ingestion_english = fields.Text(string="Ingestion (English)")
    ingestion_sinhala = fields.Text(string="Ingestion (Sinhala)")
    general_english = fields.Text(string="General (English)")
    general_sinhala = fields.Text(string="General (Sinhala)")
    appearance = fields.Many2one(comodel_name="appearance", string="Appearance")
    chemical_color = fields.Many2one(comodel_name="chemical.color", string="Color")
    odor = fields.Many2one(comodel_name="odor", string="Odor")
    stability = fields.Many2one(comodel_name="stability", string="Stability")
    incompatible_materials = fields.Many2many(comodel_name="incompatible.materials", string="Incompatible Materials")
    reactivity = fields.Many2one(comodel_name="reactivity", string="Reactivity")

    @api.onchange('categ_id')
    def onchange_categ(self):
        sample_categ_id = self.env.ref('ucwp_stock.product_category_sample')
        pro_sample_categ_id = self.env.ref('ucwp_stock.production_sample')
        dev_sample_categ_id = self.env.ref('ucwp_stock.development_sample')
        bulk_categ_id = self.env.ref('ucwp_stock.product_category_bulk')
        accessory_categ_id = self.env.ref('ucwp_stock.product_category_accessory')
        chem_categ_id = self.env.ref('ucwp_stock.product_category_chemical')
        if self.categ_id in (
                sample_categ_id, bulk_categ_id, accessory_categ_id, pro_sample_categ_id,
                dev_sample_categ_id):
            self.is_garment = True
            self.is_chemical = False
        elif self.categ_id == chem_categ_id or self.categ_id.parent_id == chem_categ_id or self.categ_id.parent_id.parent_id == chem_categ_id:
            self.is_chemical = True
            self.is_garment = False
        else:
            self.is_chemical = False
            self.is_garment = False

    @api.model
    def create(self, values):
        """ Generate sequences according to product type"""
        sequence = None
        sample_categ_id = self.env.ref('ucwp_stock.product_category_sample')
        pro_sample_categ_id = self.env.ref('ucwp_stock.production_sample')
        dev_sample_categ_id = self.env.ref('ucwp_stock.development_sample')
        bulk_categ_id = self.env.ref('ucwp_stock.product_category_bulk')
        accessory_categ_id = self.env.ref('ucwp_stock.product_category_accessory')
        chem_categ_id = self.env.ref('ucwp_stock.product_category_chemical')

        if 'categ_id' in values:
            if values['categ_id'] == chem_categ_id.id:
                sequence = self.env['ir.sequence'].next_by_code('product.chemical.number') or _('New')
                values['is_garment'] = False
                values['is_chemical'] = True
            elif values['categ_id'] == bulk_categ_id.id:
                sequence = self.env['ir.sequence'].next_by_code('product.uc.number') or _('New')
                values['is_garment'] = True
                values['is_chemical'] = False
            elif values['categ_id'] in (sample_categ_id.id, pro_sample_categ_id.id, dev_sample_categ_id.id):
                sequence = self.env['ir.sequence'].next_by_code('sample.product.number') or _('New')
                values['is_garment'] = True
                values['is_chemical'] = False
            elif values['categ_id'] in [accessory_categ_id.id]:
                values['is_garment'] = True
                values['is_chemical'] = False
            else:
                sequence = self.env['ir.sequence'].next_by_code('product.internal.reference') or _('New')
                values['is_chemical'] = False
                values['is_garment'] = False
            values['default_code'] = sequence

        # If Is Garment ticked, select by Lots for Tracking
        if 'is_garment' in values:
            if values['is_garment'] or values['is_chemical']:
                values['tracking'] = 'lot'

        return super(ProductTemplate, self).create(values)

    def write(self, vals):
        sequence = None
        sample_categ_id = self.env.ref('ucwp_stock.product_category_sample')
        pro_sample_categ_id = self.env.ref('ucwp_stock.production_sample')
        dev_sample_categ_id = self.env.ref('ucwp_stock.development_sample')
        bulk_categ_id = self.env.ref('ucwp_stock.product_category_bulk')
        accessory_categ_id = self.env.ref('ucwp_stock.product_category_accessory')
        chem_categ_id = self.env.ref('ucwp_stock.product_category_chemical')
        if 'categ_id' in vals:
            if vals['categ_id'] == chem_categ_id.id:
                sequence = self.env['ir.sequence'].next_by_code('product.chemical.number') or _('New')
                vals['is_garment'] = False
                vals['is_chemical'] = True
            elif vals['categ_id'] == bulk_categ_id.id:
                sequence = self.env['ir.sequence'].next_by_code('product.uc.number') or _('New')
                vals['is_garment'] = True
                vals['is_chemical'] = False
            elif vals['categ_id'] == sample_categ_id.id or vals['categ_id'] == pro_sample_categ_id.id or vals[
                'categ_id'] == dev_sample_categ_id.id:
                sequence = self.env['ir.sequence'].next_by_code('sample.product.number') or _('New')
                vals['is_garment'] = True
                vals['is_chemical'] = False
            elif vals['categ_id'] == accessory_categ_id.id:
                vals['is_garment'] = True
                vals['is_chemical'] = False
            vals['default_code'] = sequence
        # If Is Garment ticked, select by Lots for Tracking
        if 'is_garment' in vals:
            if vals['is_garment'] or vals['is_chemical']:
                vals['tracking'] = 'lot'
        return super(ProductTemplate, self).write(vals)

    @api.onchange('severity', 'likelihood')
    def _set_risk_rating(self):
        if self.severity and self.likelihood:
            self.risk_rating = int(self.severity) * int(self.likelihood)
        else:
            self.risk_rating = 0

    def _get_price_estimate_count(self):
        is_price_estimate_installed = self.env['ir.module.module'].search(
            [('state', '=', 'installed'), ('name', '=', 'price_estimate')])  # check module installed or not
        if self.is_garment and is_price_estimate_installed:
            price_estimate_record = self.env['pre.costing'].search([('product_id', '=', self.id)])
            if price_estimate_record:
                self.price_estimate_count = len(price_estimate_record)
            else:
                self.price_estimate_count = 0
        else:
            self.price_estimate_count = 0

    def action_view_price_estimates(self):
        is_price_estimate_installed = self.env['ir.module.module'].search(
            [('state', '=', 'installed'), ('name', '=', 'price_estimate')])  # check module installed or not
        if self.is_garment and is_price_estimate_installed:
            price_estimate_record = self.env['pre.costing'].search([('product_id', '=', self.id)])
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


class ProductProduct(models.Model):
    _inherit = "product.product"

    is_garment = fields.Boolean(string="Is Garment ?", related='product_tmpl_id.is_garment', store=True)
    is_chemical = fields.Boolean(string='Is Chemical ?', related='product_tmpl_id.is_chemical', store=True)

    # +++++++++++++++++++++++++++ Add certification to product template and product variant ++++++++++++++++++++++++++++
    available_certification = fields.Boolean(string="Available Certification")
    certification = fields.Text(string="Certification")

    # Set Active / Inactive to Product Template
    active = fields.Boolean(string="Active", default=True)

    # ++++++++++++++++++++++++++++++++++++++++++++++ Style Information +++++++++++++++++++++++++++++++++++++++++++++++++
    garment_type = fields.Many2one(comodel_name="garment.type", string="Garment Type",
                                   related='product_tmpl_id.garment_type', store=True)
    customer = fields.Many2one(comodel_name="res.partner", string="Customer", related='product_tmpl_id.customer',
                               store=True)
    buyer = fields.Many2one(comodel_name="res.partner", string="Buyer", related='product_tmpl_id.buyer', store=True)

    # ++++++++++++++++++++++++++++++++++++++++++ UCWP|IMP|-00050 MSDS II tab +++++++++++++++++++++++++++++++++++++++++++
    other_name = fields.Many2one(comodel_name="other.name", string="Other Name", related="product_tmpl_id.other_name")
    manufacturer_formulator = fields.Many2one(comodel_name="formulator", string="Manufacturer / Formulator(SDS)",
                                              related="product_tmpl_id.manufacturer_formulator")
    chemical_formulator_type = fields.Many2one(comodel_name="chemical.formulator.type",
                                               string="Chemical Formulator Type",
                                               related="product_tmpl_id.chemical_formulator_type")
    local_agent = fields.Many2one(comodel_name="res.partner", string="Local Agent",
                                  related="product_tmpl_id.local_agent")
    environment = fields.Selection([('low', 'Low'), ('medium', 'Medium'), ('high', 'High')], string="Environment",
                                   related="product_tmpl_id.environment")
    worker_health = fields.Selection([('low', 'Low'), ('medium', 'Medium'), ('high', 'High')], string="Worker Health",
                                     related="product_tmpl_id.worker_health")
    location = fields.Many2one(comodel_name="location", string="Location", related="product_tmpl_id.location")
    category = fields.Many2one(comodel_name="chemical.category", string="Category",
                               related="product_tmpl_id.category")
    chemical_type = fields.Many2one(comodel_name="chemical.type", string="Chemical Type",
                                    related="product_tmpl_id.chemical_type")
    used_for = fields.Many2one(comodel_name="chemical.used.for", string="Used for",
                               related="product_tmpl_id.used_for")
    available = fields.Boolean(string="Available", related="product_tmpl_id.available")
    issue_date = fields.Date(string="Issue Date", related="product_tmpl_id.issue_date")
    version = fields.Float(string="Version", related="product_tmpl_id.version")
    revision_date = fields.Date(string="Revision Date", related="product_tmpl_id.revision_date")
    explosive = fields.Boolean(string="Explosive", related="product_tmpl_id.explosive")
    health_hazard = fields.Boolean(string="Health Hazard", related="product_tmpl_id.health_hazard")
    flammable = fields.Boolean(string="Flammable", related="product_tmpl_id.flammable")
    environmental_hazard = fields.Boolean(string="Environmental Hazard", related="product_tmpl_id.environmental_hazard")
    toxic = fields.Boolean(string="Toxic", related="product_tmpl_id.toxic")
    corrosive = fields.Boolean(string="Corrosive", related="product_tmpl_id.corrosive")
    oxidizing = fields.Boolean(string="Oxidizing", related="product_tmpl_id.oxidizing")
    compressed_gas = fields.Boolean(string="Compressed Gas", related="product_tmpl_id.compressed_gas")
    warning_irritant = fields.Boolean(string="Warning/ Irritant", related="product_tmpl_id.warning_irritant")
    respirator = fields.Boolean(string="Respirator", related="product_tmpl_id.respirator")
    gloves = fields.Boolean(string="Gloves", related="product_tmpl_id.gloves")
    footwear = fields.Boolean(string="Foot Wear", related="product_tmpl_id.footwear")
    eye_wear = fields.Boolean(string="Eye Wear", related="product_tmpl_id.eye_wear")
    apron = fields.Boolean(string="Apron", related="product_tmpl_id.apron")
    dust_mask = fields.Boolean(string="Dust Mask", related="product_tmpl_id.dust_mask")
    overalls = fields.Boolean(string="Overalls", related="product_tmpl_id.overalls")
    face_shield = fields.Boolean(string="Face Shield", related="product_tmpl_id.face_shield")
    safety_helmet = fields.Boolean(string="Safety Helmet", related="product_tmpl_id.safety_helmet")
    measures_for_cleaning_english = fields.Text(string="Measures for Cleaning (English)",
                                                related="product_tmpl_id.measures_for_cleaning_english")
    measures_for_cleaning_sinhala = fields.Text(string="Measures for Cleaning (Sinhala)",
                                                related="product_tmpl_id.measures_for_cleaning_sinhala")
    storage_condition_english = fields.Text(string="Storage Condition (English)",
                                            related="product_tmpl_id.storage_condition_english")
    storage_condition_sinhala = fields.Text(string="Storage Condition (Sinhala)",
                                            related="product_tmpl_id.storage_condition_sinhala")
    hazard_identification_english = fields.Text(string="Hazard Identification (English)",
                                                related="product_tmpl_id.hazard_identification_english")
    hazard_identification_sinhala = fields.Text(string="Hazard Identification (Sinhala)",
                                                related="product_tmpl_id.hazard_identification_sinhala")
    health = fields.Selection(
        [('not_available', 'N/A'), ('health0', '0'), ('health1', '1'), ('health2', '2'), ('health3', '3'),
         ('health4', '4'), ('health5', '5')], string="Health", related="product_tmpl_id.health")
    flammability = fields.Selection(
        [('not_available', 'N/A'), ('flammability0', '0'), ('flammability1', '1'), ('flammability2', '2'),
         ('flammability3', '3'), ('flammability4', '4'), ('flammability5', '5')], string="Flammability",
        related="product_tmpl_id.flammability")
    reactivity_level = fields.Selection(
        [('not_available', 'N/A'), ('reactivity0', '0'), ('reactivity1', '1'), ('reactivity2', '2'),
         ('reactivity3', '3'), ('reactivity4', '4'), ('reactivity5', '5')], string="Reactivity",
        related="product_tmpl_id.reactivity_level")
    contact = fields.Selection(
        [('not_available', 'N/A'), ('contact0', '0'), ('contact1', '1'), ('contact2', '2'),
         ('contact3', '3'), ('contact4', '4'), ('contact5', '5')], string="Contact",
        related="product_tmpl_id.contact")
    severity = fields.Selection(
        [('1', '1'), ('2', '2'),
         ('3', '3'), ('4', '4'), ('5', '5')], string="Severity", related="product_tmpl_id.severity")
    likelihood = fields.Selection(
        [('1', '1'), ('2', '2'),
         ('3', '3'), ('4', '4'), ('5', '5')], string="Likelihood", related="product_tmpl_id.likelihood")
    risk_rating = fields.Integer(string="Risk Rating", related="product_tmpl_id.risk_rating")
    storage_class = fields.Many2one(comodel_name="storage.class", string="Storage Class",
                                    related="product_tmpl_id.storage_class")
    water = fields.Boolean(string="Water", related="product_tmpl_id.water")
    foom = fields.Boolean(string="Foam", related="product_tmpl_id.foom")
    dry_powder = fields.Boolean(string="Dry Powder", related="product_tmpl_id.dry_powder")
    carbon_dioxide = fields.Boolean(string="Carbon Dioxide", related="product_tmpl_id.carbon_dioxide")
    inhalation_english = fields.Text(string="Inhalation (English)", related="product_tmpl_id.inhalation_english")
    inhalation_sinhala = fields.Text(string="Inhalation (Sinhala)", related="product_tmpl_id.inhalation_sinhala")
    eye_contact_english = fields.Text(string="Eye Contact (English)", related="product_tmpl_id.eye_contact_english")
    eye_contact_sinhala = fields.Text(string="Eye Contact (Sinhala)", related="product_tmpl_id.eye_contact_sinhala")
    skin_contact_english = fields.Text(string="Skin Contact (English)", related="product_tmpl_id.skin_contact_english")
    skin_contact_sinhala = fields.Text(string="Skin Contact (Sinhala)", related="product_tmpl_id.skin_contact_sinhala")
    ingestion_english = fields.Text(string="Ingestion (English)", related="product_tmpl_id.ingestion_english")
    ingestion_sinhala = fields.Text(string="Ingestion (Sinhala)", related="product_tmpl_id.ingestion_sinhala")
    general_english = fields.Text(string="General (English)", related="product_tmpl_id.general_english")
    general_sinhala = fields.Text(string="General (Sinhala)", related="product_tmpl_id.general_sinhala")
    appearance = fields.Many2one(comodel_name="appearance", string="Appearance",
                                 related="product_tmpl_id.appearance")
    chemical_color = fields.Many2one(comodel_name="chemical.color", string="Color",
                                     related="product_tmpl_id.chemical_color")
    odor = fields.Many2one(comodel_name="odor", string="Odor", related="product_tmpl_id.odor")
    stability = fields.Many2one(comodel_name="stability", string="Stability", related="product_tmpl_id.stability")
    incompatible_materials = fields.Many2many(comodel_name="incompatible.materials", string="Incompatible Materials",
                                              related="product_tmpl_id.incompatible_materials")
    reactivity = fields.Many2one(comodel_name="reactivity", string="Reactivity",
                                 related="product_tmpl_id.reactivity")

    # ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

    @api.model
    def create(self, values):
        if 'product_tmpl_id' in values:
            product_template = values['product_tmpl_id']
            product_tmpl = self.env['product.template'].browse(product_template)
            values['default_code'] = product_tmpl.default_code

        return super(ProductProduct, self).create(values)

    def action_style_expire(self):
        """Check conditions to set Styles Archive"""
        set_days = self.env['res.config.settings'].search([('style_expire', '=', True)], order="id desc", limit=1)
        if set_days:
            number_of_days = set_days.days
            current_date = datetime.today()
            from_date = current_date - timedelta(days=number_of_days)

            active_product_variants = self.env['product.product'].search(
                [('active', '=', True), ('is_garment', '=', True)])
            if active_product_variants:
                for active_product_variant in active_product_variants:
                    product_qty_available = active_product_variant.qty_available

                    picking_records = self.env['stock.picking'].search(
                        [('scheduled_date', '<', from_date),
                         ('picking_type_id.code', 'in', ['outgoing', 'incoming']),
                         ('state', 'not in', ['draft', 'cancel'])])
                    picking_available = False
                    if picking_records:
                        for picking_record in picking_records:
                            for picking_line in picking_record.move_ids_without_package:
                                if picking_line.product_id.id == active_product_variant.id:
                                    picking_available = True
                    if picking_available is False and product_qty_available > 0:
                        self.env['style.archive.approval'].create({
                            'product_id': active_product_variant.id,
                            'state': 'draft',
                        })
                    elif picking_available is False and product_qty_available <= 0:
                        active_product_variant.write({
                            'active': False
                        })


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    style_expire = fields.Boolean(string="Style Expire Timer",
                                  config_parameter='ucwp_stock.style_expire')
    days = fields.Integer(string="Days",
                          config_parameter='ucwp_stock.days')

    @api.model
    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        res.update(
            style_expire=self.env['ir.config_parameter'].sudo().get_param(
                'ucwp_stock.style_expire'),
            days=self.env['ir.config_parameter'].sudo().get_param(
                'ucwp_stock.days'),
        )
        return res

    def set_values(self):
        super(ResConfigSettings, self).set_values()
        param = self.env['ir.config_parameter'].sudo()

        style_expire = self.style_expire or False
        days = self.days or False

        param.set_param('ucwp_stock.style_expire', style_expire)
        param.set_param('ucwp_stock.days', days)


class ChemicalStandards(models.Model):
    _name = "chemical.standards"
    _description = "Chemical Standards"

    name = fields.Char(string="Name")
    # Attachment Field for Chemical Standards in Product
    document = fields.Many2many(comodel_name="ir.attachment", attachment=True, string="Document")
    product_tmpl_id = fields.Many2one(comodel_name="product.product", string="Product Template ID")


class LabReports(models.Model):
    _name = "lab.reports"
    _description = "Lab Reports"

    name = fields.Char(string="Report Name")
    # Attachment Field for Test/Lab Reports in Product
    document = fields.Many2many(comodel_name="ir.attachment", attachment=True, string="Report Files")
    product_template_id = fields.Many2one(comodel_name="product.product", string="Product Template ID")


class StyleArchiveApproval(models.Model):
    """ archive product with stock but not used for long time"""
    _name = "style.archive.approval"
    _description = "Style Archive Approval"
    _rec_name = "product_id"

    product_id = fields.Many2one(comodel_name="product.product", string="Product", required=True)
    state = fields.Selection([('draft', 'Draft'), ('approved', 'Approved')], string="Status", default='draft')

    def action_approve(self):
        """Approve record and set product inactive"""
        self.write({'state': 'approved'})
        self.product_id.active = False

    def action_set_to_draft(self):
        """Approve record and set product active"""
        self.write({'state': 'draft'})
        self.product_id.active = True


# UCWP|IMP|-00050 MSDS New fields
class OtherName(models.Model):
    _name = "other.name"

    name = fields.Text(string="Name")


class ChemicalFormulatorType(models.Model):
    _name = "chemical.formulator.type"

    name = fields.Text(string="Chemical Formulator Type")


class Formulator(models.Model):
    _name = "formulator"

    name = fields.Text(string="Name")


class Location(models.Model):
    _name = "location"

    name = fields.Text(string="Location")


class ChemicalCategory(models.Model):
    _name = "chemical.category"

    name = fields.Text(string="Chemical Category")


class ChemicalType(models.Model):
    _name = "chemical.type"

    name = fields.Text(string="Chemical Type")


class ChemicalUsedFor(models.Model):
    _name = "chemical.used.for"

    name = fields.Text(string="Chemical Used for")


class StorageClass(models.Model):
    _name = "storage.class"

    name = fields.Text(string="Name")


class Appearance(models.Model):
    _name = "appearance"

    name = fields.Text(string="Appearance")


class ChemicalColor(models.Model):
    _name = "chemical.color"

    name = fields.Text(string="Color")


class Odor(models.Model):
    _name = "odor"

    name = fields.Text(string="Odor")


class Stability(models.Model):
    _name = "stability"

    name = fields.Text(string="Stability")


class IncompatibleMaterials(models.Model):
    _name = "incompatible.materials"

    name = fields.Text(string="Materials")


class Reactivity(models.Model):
    _name = "reactivity"

    name = fields.Text(string="Reactivity")
