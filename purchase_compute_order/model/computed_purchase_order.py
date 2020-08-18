# -*- encoding: utf-8 -*-
##############################################################################
#
#    Purchase - Computed Purchase Order Module for Odoo
#    Copyright (C) 2013-Today GRAP (http://www.grap.coop)
#    @author Julien WESTE
#    @author Sylvain LE GAL (https://twitter.com/legalsylvain)
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
import datetime
import time
import logging
from math import ceil
from openerp import models, fields, api, _, exceptions
import openerp.addons.decimal_precision as dp
from openerp.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class ComputedPurchaseOrder(models.Model):
    _description = 'Computed Purchase Order'
    _name = 'computed.purchase.order'
    _order = 'id desc'

    # Constant Values
    _DEFAULT_NAME = _('New')

    @api.model
    def _get_state_selection(self):
        return [
            ('draft', 'Draft'),
            ('done', 'Done'),
            ('canceled', 'Canceled')
        ]

    @api.model
    def _get_target_type_selection(self):
        return [
            ('product_price_inv', '€'),
            ('time', 'days'),
            ('weight_net', 'kg')
        ]

    @api.model
    def _get_product_price_selection(self):
        return [
            ('product_price', 'Product price'),
            ('last_purchase', 'Last purchase price'),
            ('last_purchase_supplier', 'Last purchase of the supplier')
        ]

    # # Fields Function section
    # @api.multi
    # def _get_stock_line_ids(self):
    #     for computed_po in self:
    #         self.stock_line_ids = [x.id for x in computed_po.line_ids]

    @api.multi
    def _get_computed_amount_duration(self):
        for cpo in self:
            min_duration = 999
            amount = 0
            for line in cpo.line_ids:
                if line.average_consumption != 0:
                    duration = (line.computed_qty + line.purchase_qty)\
                        / line.average_consumption
                    min_duration = min(duration, min_duration)
                amount += line.purchase_qty * line.product_price_inv
            cpo.computed_amount = amount
            cpo.computed_duration = min_duration

    @api.multi
    def _get_products_updated(self):
        for cpo in self:
            updated = False
            for line in cpo.line_ids:
                if line.state == 'updated':
                    updated = True
                    break
            cpo.products_updated = updated

    name = fields.Char(
        'Computed Purchase Order Reference', size=64, required=True,
        readonly=True,
        help="""Unique number of the automated purchase order, computed"""
        """ automatically when the computed purchase order is created.""",
        default=_DEFAULT_NAME)
    company_id = fields.Many2one(
        'res.company', string='Company', readonly=True, required=True,
        help="""When you will validate this item, this will create a"""
        """ purchase order for this company.""",
        default=(
            lambda s: s.env['res.users']._get_company()))
    active = fields.Boolean(
        'Active',
        help="""By unchecking the active field, you may hide this item"""
        """ without deleting it.""",
        default=True)
    state = fields.Selection('_get_state_selection', 'State', required=True,
                             default='draft')
    incoming_date = fields.Date('Wished Incoming Date',
                                help="Wished date for products delivery.")
    partner_id = fields.Many2one(
        'res.partner', string='Supplier', required=True,
        domain=[('supplier', '=', True)],
        help="Supplier of the purchase order.")
    line_ids = fields.One2many(
        'computed.purchase.order.line', 'computed_purchase_order_id',
        string='Order Lines', help="Products to order.",
        ondelete='cascade')

    # this is to be able to display the line_ids on 2 tabs of the view
    # TODO: If not works add compute: compute='_get_stock_line_ids',
    stock_line_ids = fields.One2many(
        'computed.purchase.order.line', 'computed_purchase_order_id',
        help="Products to order.")
    compute_pending_quantity = fields.Boolean(
        'Pending quantity taken in account', default=True)
    compute_draft_quantity = fields.Boolean('Draft quantity taken in account',
                                            default=True)
    purchase_order_id = fields.Many2one(
        'purchase.order', string='Purchase Order', readonly=True)
    purchase_target = fields.Integer('Purchase Target', default=0)
    target_type = fields.Selection(
        '_get_target_type_selection', 'Target Type', required=True,
        help="""This defines the amount of products you want to"""
        """ purchase. \n"""
        """The system will compute a purchase order based on the stock"""
        """ you have and the average consumption of each product."""
        """ * Target type '€': computed purchase order will cost at"""
        """ least the amount specified\n"""
        """ * Target type 'days': computed purchase order will last"""
        """ at least the number of days specified (according to current"""
        """ average consumption)\n"""
        """ * Target type 'kg': computed purchase order will weight at"""
        """ least the weight specified""", default='product_price_inv')
    computed_amount = fields.Float(
        string='Amount of the computed order',
        digits_compute=dp.get_precision('Product Price'),
        compute='_get_computed_amount_duration',
        multi='computed_amount_duration')
    computed_duration = fields.Integer(
        string='Minimum duration after order',
        compute='_get_computed_amount_duration',
        multi='computed_amount_duration')
    products_updated = fields.Boolean(
        string='Indicate if there were any products updated in the list',
        compute='_get_products_updated'
    )
    created_date = fields.Date('Create Date',
                               default=lambda *a: time.strftime('%Y-%m-%d'))
    confirm_date = fields.Date('Confirm Date')
    growth_factor = fields.Float('Growth Factor')
    product_price = fields.Selection(
        '_get_product_price_selection',
        'Product price based on', default='product_price')
    last_job = fields.Many2one(
        comodel_name='queue.job',
        string="Update computed Job", readonly=True, copy=False,
    )

    # View Section
    @api.onchange('partner_id')
    def onchange_partner_id(self):
        # TODO: create a wizard to validate the change
        self.purchase_target = 0
        self.target_type = 'product_price_inv'
        if self.partner_id:
            partner = self.partner_id
            self.purchase_target = partner.purchase_target
            self.target_type = partner.target_type
        if self.line_ids:
            self.line_ids = [(2, x.id, False) for x in self.line_ids]

    # Overload Section
    @api.model
    def create(self, vals):
        if vals.get('name', self._DEFAULT_NAME) == self._DEFAULT_NAME:
            vals['name'] = self.env['ir.sequence'].get(
                'computed.purchase.order') or '/'
        return super(ComputedPurchaseOrder, self).create(vals)

    @api.multi
    def write(self, values):
        cpo_id = super(ComputedPurchaseOrder, self).write(values)
        if self.update_sorting(values):
            self._sort_lines()
        return cpo_id

    @api.model
    def update_sorting(self, values):
        try:
            context = self.env.context
            line_ids = values.get('line_ids', False)
            if not line_ids:
                return False

            # this context check will allow you to change the field list
            # without overriding the whole function
            need_sorting_fields = context.get('need_sorting_fields', False)
            if not need_sorting_fields:
                need_sorting_fields = [
                    'average_consumption',
                    'computed_qty',
                    'stock_duration',
                    'manual_input_output_qty',
                ]
            for value in line_ids:
                if len(value) > 2 and value[2] and isinstance(value[2], dict)\
                        and (set(need_sorting_fields) & set(value[2].keys())):
                    return True
            return False

        except:
            return False

    # Private Section
    @api.multi
    def _sort_lines(self):
        cpol_obj = self.env['computed.purchase.order.line']
        for cpo in self:
            lines = cpo.line_ids
            lines = sorted(
                lines, key=lambda line: line.average_consumption,
                reverse=True)
            lines = sorted(lines, key=lambda line: line.stock_duration)

            id_index_list = {}
            for i in lines:
                id_index_list[i['id']] = lines.index(i)
            for line_id in list(id_index_list.keys()):
                line = cpol_obj.browse(line_id)
                line.write({'sequence': id_index_list[line_id]})

    @api.multi
    def _make_po_lines(self):
        self.ensure_one()
        all_lines = []
        for line in self.line_ids:
            if line.purchase_qty != 0:
                line_values = self.write_line_values(line)
                all_lines.append((0, 0, line_values),)
        return all_lines

    @api.multi
    def write_line_values(self, line):
        line_values = {
            'name': line.product_id.display_name,
            'product_qty': line.purchase_qty,
            'date_planned': (
                self.incoming_date or fields.Date.context_today(self)),
            'product_uom': line.product_id.uom_po_id.id,
            'product_id': line.product_id.id,
            'price_unit': line.product_price_inv,
            'taxes_id': [(
                6, 0,
                [x.id for x in line.product_id.supplier_taxes_id])],
        }
        return line_values

    @api.multi
    def _compute_purchase_quantities_days(self):
        self.ensure_one()
        psi_env = self.env['product.supplierinfo']
        days = self.purchase_target
        for line in self.line_ids:
            package_quantity = 1
            temp_value = 0
            if line.average_consumption:
                quantity = max(
                    days * line.average_consumption * line.uom_po_id.factor /
                    line.uom_id.factor - line.computed_qty, 0)
                if self.growth_factor != 0:
                    quantity_growth_factor = (
                        quantity * self.growth_factor / 100)
                    quantity = quantity + round(quantity_growth_factor)
                # if (hasattr(line.supplier,
                #             'qty_multiple') and line.supplier.qty_multiple):
                #     package_quantity = line.supplier.qty_multiple
                #     temp_value = quantity
                #     resto = quantity % package_quantity
                #     quantity = quantity + package_quantity - resto
            else:
                quantity = -line.computed_qty
            if hasattr(psi_env, 'discount'):
                psi = psi_env.search([
                    ('name', '=', self.partner_id.id),
                    ('product_tmpl_id', '=',
                     line.product_id.product_tmpl_id.id),
                    ('min_qty', '<=', quantity)
                ], order='price, discount desc', limit=1)
            else:
                psi = psi_env.search([
                    ('name', '=', self.partner_id.id),
                    ('product_tmpl_id', '=',
                     line.product_id.product_tmpl_id.id),
                    ('min_qty', '<=', quantity)
                ], order='price', limit=1)
            if psi:
                package_quantity = hasattr(
                    line.supplier,
                    'qty_multiple') and psi.qty_multiple or 1
                temp_value = quantity
                resto = quantity % package_quantity
                if resto:
                    quantity = quantity + package_quantity - resto
            line.write({'purchase_qty': quantity or 0,
                        'temp_value': temp_value,
                        'supplier': psi.id}
                       )
        return True

    @api.multi
    def _compute_purchase_quantities_other(self, field=None):
        self.ensure_one()
        cpo = self
        psi_env = self.env['product.supplierinfo']
        if not cpo.line_ids:
            return False
        target = cpo.purchase_target
        ok = False
        days = -1
        field_list = cpo.line_ids.read([field])
        field_list_dict = {}
        for i in field_list:
            field_list_dict[i['id']] = i[field]
        while not ok:
            days += 1
            qty_tmp = {}
            for line in cpo.line_ids:
                package_quantity = 1
                temp_value = 0
                quantity = 0
                if line.average_consumption:
                    quantity = max(
                        days * line.average_consumption *
                        line.uom_po_id.factor / line.uom_id.factor -
                        line.computed_qty, 0)
                    if quantity == 0 and line.computed_qty < 0:
                        quantity = line.computed_qty * -1
                elif line.computed_qty < 0:
                    quantity = line.computed_qty * -1
                if hasattr(psi_env, 'discount'):
                    psi = psi_env.search([
                        ('name', '=', self.partner_id.id),
                        ('product_tmpl_id', '=',
                         line.product_id.product_tmpl_id.id),
                        ('min_qty', '<=', quantity)
                    ], order='price, discount desc', limit=1)
                else:
                    psi = psi_env.search([
                        ('name', '=', self.partner_id.id),
                        ('product_tmpl_id', '=',
                         line.product_id.product_tmpl_id.id),
                        ('min_qty', '<=', quantity)
                    ], order='price', limit=1)
                if psi:
                    package_quantity = hasattr(
                        line.supplier,
                        'qty_multiple') and psi.qty_multiple or 1
                    temp_value = quantity
                    resto = quantity % package_quantity
                    if resto:
                        quantity = quantity + package_quantity - resto
                qty_tmp[line.id] = [quantity, temp_value, psi]
            ok = self._check_purchase_qty(
                target, field_list_dict, qty_tmp)

        for line in cpo.line_ids:
            line.write({'purchase_qty': qty_tmp[line.id][0],
                        'temp_value': qty_tmp[line.id][1],
                        'supplier': qty_tmp[line.id][2].id}
                       )
        return True

    @api.model
    def _check_purchase_qty(self, target=0, field_list=None, qty_tmp=None):
        if not target or field_list is None or qty_tmp is None:
            return True
        total = 0
        for key in list(field_list.keys()):
            total += field_list[key] * qty_tmp[key][0]
        if total == 0.0 and total < target:
            raise exceptions.Warning(_(
                'Total returned while computing purchase target is 0. '
                'The purchase target is set to %s and is not possible to '
                'reach the defined target. '
                'Please check lines if they have price/weight defined') % (
                    target))
        return total >= target

    @api.multi
    def _active_product_stock_product_domain(self, psi_ids):
        self.ensure_one()
        if not psi_ids:
            raise ValidationError("No hay productos con ese proveedor")
        self.env.cr.execute("""
            SELECT product_tmpl_id
            FROM product_supplierinfo
            WHERE id in %s
              AND product_tmpl_id is not null
        """, (tuple(psi_ids),))
        result = self.env.cr.fetchall()
        tmpl_ids = [r[0] for r in result]
        product_domain = [
            ('product_tmpl_id', 'in', tmpl_ids)
        ]
        return product_domain

    @api.multi
    def _get_product_supplierinfo(self):
        self.ensure_one()
        psi_obj = self.env['product.supplierinfo']
        return psi_obj.search([
            ('name', '=', self.partner_id.id)
        ])

    # Action section
    @api.multi
    def compute_active_product_stock(self):
        pp_obj = self.env['product.product']
        for cpo in self:
            cpol_list = []
            # TMP delete all rows,
            # TODO : depends on further request to avoid user data to be lost
            cpo.mapped('line_ids').unlink()

            # Get product_product and compute stock
            psi_ids = cpo._get_product_supplierinfo()
            # Already created product lines in cpol. Used to avoid line
            # duplication when supplier is defined in variants
            cpol_product_ids = []
            product_domain = self._active_product_stock_product_domain(
                psi_ids.ids)
            pp_ids = pp_obj.search(product_domain)
            pp_ids.refresh()  # Clear product cache
            for pp in pp_ids:
                if pp.id not in cpol_product_ids:
                    psi = [ps for ps in pp.seller_ids
                           if ps.name.id == cpo.partner_id.id]
                    cpol_list.append((0, 0, {
                        'product_id': pp.id,
                        'state': 'up_to_date',
                        'product_code': psi and psi[0].product_code,
                        'product_name': psi and psi[0].product_name,
                        'package_quantity': psi and (
                             (hasattr(psi[0], 'qty_multiple') and
                              psi[0].qty_multiple)) or 1.0,
                        # 'package_quantity': psi and (
                        #     (hasattr(psi[0], 'package_qty') and
                        #      psi[0].package_qty) or psi[0].min_qty) or 1.0,
                        'average_consumption': pp.average_consumption,
                        'uom_po_id':
                            psi and psi[0].product_uom.id or pp.uom_po_id.id,
                    }))
                    cpol_product_ids.append(pp.id)
            # update line_ids
            self.write_active_product_stock(cpo, cpol_list)
        return True

    @api.multi
    def write_active_product_stock(self, cpo, cpol_list):
        cpo.write({'line_ids': cpol_list})

    @api.multi
    def compute_purchase_quantities(self):
        self.ensure_one()
        cpo = self
        if cpo.target_type == 'time':
            res = self._compute_purchase_quantities_days()
        else:
            res = self._compute_purchase_quantities_other(
                field=cpo.target_type)
        return res

    @api.multi
    def update_computed_qty(self):
        job_env = self.env['queue.job']
        job_delay = self.line_ids.with_delay()._get_computed_qty()
        job = job_env.search([
            ('uuid', '=', job_delay.uuid)
        ], limit=1)
        self.write({
            'last_job': job.id
        })

    @api.multi
    def _get_purchase_order_vals(self, po_lines):
        self.ensure_one
        company = self.env.user.company_id
        partner = self.partner_id
        return {
            'origin': self.name,
            'partner_id': partner.id,
            'location_id': company.partner_id.property_stock_customer.id,
            'pricelist_id': partner.property_product_pricelist.id,
            'order_line': po_lines,
            'computed_order': self.id,
        }

    @api.multi
    def _open_purchase_order_action(self, purchase_id):
        mod_obj = self.env['ir.model.data']
        res = mod_obj.get_object_reference('purchase', 'purchase_order_form')
        res_id = res and res[1] or False
        return {
            'name': _('Purchase Order'),
            'view_type': 'form',
            'view_mode': 'form',
            'view_id': [res_id],
            'res_model': 'purchase.order',
            'type': 'ir.actions.act_window',
            'nodestroy': True,
            'target': 'current',
            'res_id': purchase_id or False,
        }

    @api.multi
    def make_order(self):
        self.ensure_one
        po_lines = self._make_po_lines()
        if not po_lines:
            raise exceptions.Warning(
                _('All purchase quantities are set to 0!'))

        po_obj = self.env['purchase.order']
        po_values = self._get_purchase_order_vals(po_lines)
        po_id = po_obj.create(po_values)
        self.write({
            'state': 'done',
            'purchase_order_id': po_id.id,
            'confirm_date': datetime.datetime.now()
        })

        return self._open_purchase_order_action(po_id.id)
