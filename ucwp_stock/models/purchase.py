from odoo import api, fields, models, _


class PurchaseOrder(models.Model):
    _inherit = "purchase.order.line"

    @api.onchange('product_id')
    def _filter_product(self):
        products = self.env['product.product'].search([], order='id ASC')
        chemical_products = []
        if products:
            for product in products:
                if product.product_tmpl_id.is_chemical:
                    if product.variant_seller_ids:
                        for seller_id in product.variant_seller_ids:
                            if seller_id.name == self.order_id.partner_id:
                                chemical_products.append(product.id)
        return {'domain': {'product_id': [('id', 'in', chemical_products)]}}
