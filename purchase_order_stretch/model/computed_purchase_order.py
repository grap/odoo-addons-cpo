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
        values['name'] =\
            line.supplier.product_name or line.product_id.display_name
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
        ], order='price, discount desc', limit=1)
        if not psi:
            return super(ComputedPurchaseOrderLine,
                         self)._line_product_supplier_info()
        return psi

    @api.multi
    def _line_product_supplier_info_change(self, purchase_qty):
        self.ensure_one()
        cpo_partner_id = self.computed_purchase_order_id.partner_id.id
        product_tmpl_id = self.product_id.product_tmpl_id.id
        psi = self.env['product.supplierinfo'].search([
            ('name', '=', cpo_partner_id),
            ('product_tmpl_id', '=', product_tmpl_id),
            ('min_qty', '<=', purchase_qty)
        ], order='price, discount desc', limit=1)
        return psi

    @api.multi
    def _update_quantity(self, psi, purchase_qty):
        if self.temp_value and self.temp_value != purchase_qty and\
                hasattr(psi, 'qty_multiple'):
            package_quantity = psi.qty_multiple or 1
            resto = self.temp_value % package_quantity
            if resto:
                quantity = self.temp_value + package_quantity - resto
            else:
                quantity = self.temp_value
            if hasattr(self, 'supplier_multiple'):
                # self.temp_value = self.purchase_qty
                # self.purchase_qty = quantity
                # self.supplier_multiple = package_quantity
                # self.product_code_inv = psi.product_code
                # self.product_name_inv = psi.product_name
                # self.product_price_inv = self._product_price_based_on(True)
                # self.supplier = psi
                return {
                    'temp_value': self.purchase_qty,
                    'purchase_qty': quantity or package_quantity or 0,
                    'supplier_multiple': package_quantity,
                    'product_code_inv': psi.product_code,
                    'product_name_inv': psi.product_name,
                    'product_price_inv': self._product_price_based_on(True),
                    'supplier': psi.id
                }
        return False

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
                    line_dict = cpol._update_quantity(psi, cpol.purchase_qty)
                    if line_dict:
                        cpol.write({'purchase_qty': line_dict['purchase_qty']})
                        cpol.update(line_dict)
                    else:
                        resto = cpol.purchase_qty %\
                            (cpol.supplier_multiple or 1)
                        if resto:
                            cpol.purchase_qty = cpol.purchase_qty +\
                                cpol.supplier_multiple - resto
                        cpol.product_code_inv = psi.product_code
                        cpol.product_name_inv = psi.product_name
                        cpol.product_price_inv = cpol._product_price_based_on(
                            True)
                        cpol.supplier = psi
                        cpol.package_quantity_inv = (
                            hasattr(psi,
                                    'qty_multiple') and psi.qty_multiple or 1.0)

    @api.onchange('purchase_qty')
    def _on_change_purchase_qty(self):
        for cpol in self:
            if not cpol.product_id:
                cpol.product_code_inv = None
                cpol.product_name_inv = None
                cpol.product_price_inv = 0.0
                cpol.package_quantity_inv = 0.0
            else:
                psi = cpol._line_product_supplier_info()
                if psi:
                    package_quantity = hasattr(
                        cpol.supplier,
                        'qty_multiple') and psi.qty_multiple or 1
                    quantity = cpol.purchase_qty
                    temp_value = quantity
                    resto = quantity % package_quantity
                    if resto:
                        cpol.temp_value = temp_value
                        quantity = quantity + package_quantity - resto
                    psi2 = cpol._line_product_supplier_info_change(quantity)
                    line_dict = cpol._update_quantity(psi2, quantity)
                    if line_dict:
                        cpol.write({'purchase_qty': line_dict['purchase_qty']})
                        cpol.update(line_dict)
                    else:
                        package_quantity = hasattr(psi, 'qty_multiple') and psi.qty_multiple or 1
                        resto = quantity % package_quantity
                        if resto:
                            quantity = quantity + package_quantity - resto
                        cpol.product_code_inv = psi.product_code
                        cpol.product_name_inv = psi.product_name
                        cpol.product_price_inv = cpol._product_price_based_on(
                            True)
                        cpol.supplier = psi
                        cpol.package_quantity_inv = package_quantity
                        cpol.purchase_qty = quantity
                        cpol['purchase_qty'] = quantity
