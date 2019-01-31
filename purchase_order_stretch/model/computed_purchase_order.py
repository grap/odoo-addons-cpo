# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
# © 2018 FactorLibre - Álvaro Marcos <alvaro.marcos@factorlibre.com>
from openerp import models, api, fields
import openerp.addons.decimal_precision as dp


class ComputedPurchaseOrder(models.Model):
    _inherit = 'computed.purchase.order'

    @api.multi
    def write_line_values(self, line):
        values = super(ComputedPurchaseOrder, self).write_line_values(line)
        values['supplier_id'] = line.supplier.id
        values['name'] = line.product_name or line.product_id.display_name
        return values


class ComputedPurchaseOrderLine(models.Model):
    _inherit = 'computed.purchase.order.line'

    product_code_inv = fields.Char(
        'Supplier Product Code',
        compute='_update_product_information', inverse='_set_product_code',
        help="""This supplier's product code will be used when printing"""
        """ a request for quotation. Keep empty to use the internal"""
        """ one.""")
    product_name = fields.Char('Supplier Product Name')
    product_name_inv = fields.Char(
        'Supplier Product Name',
        compute='_update_product_information', inverse='_set_product_name',
        help="""This supplier's product name will be used when printing"""
        """ a request for quotation. Keep empty to use the internal"""
        """ one.""")
    product_price = fields.Float(
        'Supplier Product Price',
        digits_compute=dp.get_precision('Product Price'))
    product_price_inv = fields.Float(
        'Supplier Product Price',
        compute='_update_product_information', inverse='_set_product_price')
    package_quantity = fields.Float('Package quantity')
    package_quantity_inv = fields.Float(
        'Package quantity', compute='_update_product_information',
        inverse='_set_package_quantity')

    @api.multi
    def _line_product_supplier_info(self):
        self.ensure_one()
        cpo_partner_id = self.computed_purchase_order_id.partner_id.id
        product_tmpl_id = self.product_id.product_tmpl_id.id
        psi = self.env['product.supplierinfo'].search([
            ('name', '=', cpo_partner_id),
            ('product_tmpl_id', '=', product_tmpl_id),
            ('min_qty', '<=', self.purchase_qty)
        ], order='price', limit=1)
        if not psi:
            return super(ComputedPurchaseOrderLine,
                         self)._line_product_supplier_info()
        return psi

    @api.onchange('purchase_qty')
    @api.multi
    def _update_product_information(self):
        for cpol in self:
            if not cpol.product_id:
                cpol.product_code_inv = None
                cpol.product_name_inv = None
                cpol.product_price_inv = 0.0
                cpol.package_quantity_inv = 0.0
            else:
                psi = cpol._line_product_supplier_info()
                if psi:
                    cpol.product_code_inv = psi.product_code
                    cpol.product_name_inv = psi.product_name
                    cpol.product_price_inv = cpol._product_price_based_on(True)
                    cpol.supplier = psi
                    cpol.package_quantity_inv = (
                        hasattr(psi, 'package_qty') and psi.package_qty or 1.0)
