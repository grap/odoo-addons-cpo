# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
# © 2018 FactorLibre - Álvaro Marcos <alvaro.marcos@factorlibre.com>
from openerp import models, fields, api
from odoo.exceptions import ValidationError


class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    @api.multi
    def _get_product_tmpl(self):
        for line in self:
            if line.product_id.product_tmpl_id:
                line.product_tmpl_id = line.product_id.product_tmpl_id

    supplier_id = fields.Many2one('product.supplierinfo', 'Proveedor')
    product_tmpl_id = fields.Many2one('product.template', 'Plantilla',
                                      compute='_get_product_tmpl')

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
    def update_line(self, supplier):
        self.ensure_one
        data_dict = {
            'name': supplier.product_name or self.product_id.name or "",
            'product_qty': supplier.min_qty or 1,
            'price_unit': supplier.price or self.product_id.standard_price,
            'discount': supplier.discount or 0,
        }
        self.update(data_dict)

    @api.onchange('product_id')
    def onchange_product_id_supp(self):
        for line in self:
            if len(line.order_id.order_line.filtered(
                    lambda r: r.product_id == line.product_id)) > 2:
                raise ValidationError((
                    "Ya hay una línea para este producto"))
            if line.product_id.product_tmpl_id.id:
                psi = self.env['product.supplierinfo'].search([
                    ('name', '=', line.order_id.partner_id.id),
                    ('product_tmpl_id', '=',
                     line.product_id.product_tmpl_id.id),
                ], order='sequence', limit=1)
                if psi:
                    line.supplier_id = psi
                else:
                    line.supplier_id = False
            else:
                line.supplier_id = False
            # product = line.product_id
            # line.name = "[%s] %s" % (product.default_code, product.name)
            line._get_product_tmpl()


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    @api.onchange('partner_id')
    def onchange_partner(self):
        for order in self:
            for line in order.order_line:
                psi = False
                if line.product_id.product_tmpl_id.id:
                    psi = self.env['product.supplierinfo'].search([
                        ('name', '=', line.order_id.partner_id.id),
                        ('product_tmpl_id', '=',
                         line.product_id.product_tmpl_id.id),
                    ], order='sequence', limit=1)
                    if psi:
                        line.supplier_id = psi
                    else:
                        line.supplier_id = False
                else:
                    line.supplier_id = False
                # product = line.product_id
                # line.name = "[%s] %s" % (product.default_code, product.name)
                line._get_product_tmpl()
                line.update_line(psi)


class ProductSupplierinfo(models.Model):
    _inherit = 'product.supplierinfo'

    @api.multi
    def name_get(self):
        return [(s.id, "%s - %s" % (s.name.name, s.product_name))
                for s in self]
