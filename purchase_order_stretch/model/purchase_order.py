# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
# © 2018 FactorLibre - Álvaro Marcos <alvaro.marcos@factorlibre.com>
from openerp import models, fields, api


class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    @api.onchange('supplier_id')
    def onchange_supplier(self):
        data_dict = {
            'name': self.supplier_id.product_name or self.product_id.name,
            'product_qty': self.supplier_id.min_qty,
            'price_unit': self.supplier_id.price,
            'discount': self.supplier_id.discount,
        }
        self.update(data_dict)

    @api.multi
    def _get_product_tmpl(self):
        for line in self:
            if line.product_id.product_tmpl_id:
                line.product_tmpl_id = line.product_id.product_tmpl_id

    supplier_id = fields.Many2one('product.supplierinfo', 'Proveedor')
    product_tmpl_id = fields.Many2one('product.template', 'Plantilla',
                                      compute='_get_product_tmpl')

    @api.onchange('product_id')
    def onchange_product_id_supp(self):
        for line in self:
            line.supplier_id = False
            product = line.product_id
            line.name = "[%s] %s" % (product.default_code, product.name)
            line._get_product_tmpl()


class ProductSupplierinfo(models.Model):
    _inherit = 'product.supplierinfo'

    @api.multi
    def name_get(self):
        return [(s.id, "%s - %s" % (s.name.name, s.product_name))
                for s in self]
