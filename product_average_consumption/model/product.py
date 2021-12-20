##############################################################################
#
#    Product - Average Consumption Module for Odoo
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
import time
import datetime
from odoo import models, fields, api, _
from odoo.tools import pycompat
from odoo.tools.float_utils import float_round


class ProductProduct(models.Model):
    _inherit = "product.product"

    average_consumption = fields.Float(
        compute='_average_consumption',
        string='Average Consumption (max 365 days)')
    total_consumption = fields.Float(
        compute='_average_consumption',
        string='Total Consumption (ud. max 365 days)')
    average_consumption_15 = fields.Float(
        compute='_average_consumption',
        string='Average Consumption (15 days)')
    total_consumption_15 = fields.Float(
        compute='_average_consumption',
        string='Total Consumption (ud. 15 days)')
    average_consumption_30 = fields.Float(
        compute='_average_consumption',
        string='Average Consumption (30 days)')
    total_consumption_30 = fields.Float(
        compute='_average_consumption',
        string='Total Consumption (ud. 30 days)')
    average_consumption_90 = fields.Float(
        compute='_average_consumption',
        string='Average Consumption (90 days)')
    total_consumption_90 = fields.Float(
        compute='_average_consumption',
        string='Total Consumption (ud. 90 days)')
    nb_days = fields.Float(
        compute='_average_consumption',
        string='Number of days for the calculation',
        help="""The calculation will be done for the last 365 days or"""
        """ since the first purchase or sale of the product if it's"""
        """ more recent""")

    @api.multi
    def _min_date(self):
        self.ensure_one()
        query = """SELECT to_char(min(date), 'YYYY-MM-DD') \
                from stock_move
                where product_id = %s
                GROUP BY product_id""" % (self.id)
        self.env.cr.execute(query)
        results = self.env.cr.fetchall()
        return results and results[0] and results[0][0] \
            or time.strftime('%Y-%m-%d')

    @api.multi
    def _average_consumption(self):
        self.refresh()
        product_consumption = self.calculate_average_days_dict(365)
        product_consumption_15 = self.calculate_average_days_dict(15)
        product_consumption_30 = self.calculate_average_days_dict(30)
        product_consumption_90 = self.calculate_average_days_dict(90)
        for product in self:
            product.nb_days = product_consumption[product.id]['nb_days']
            product.average_consumption = product_consumption[product.id][
                'average_consumption']
            product.total_consumption = product_consumption[product.id][
                'total_consumption']
            product.average_consumption_15 = product_consumption_15[
                product.id]['average_consumption_15']
            product.total_consumption_15 = product_consumption_15[product.id][
                'total_consumption_15']
            product.average_consumption_30 = product_consumption_30[
                product.id]['average_consumption_30']
            product.total_consumption_30 = product_consumption_30[product.id][
                'total_consumption_30']
            product.average_consumption_90= product_consumption_90[
                product.id]['average_consumption_90']
            product.total_consumption_90 = product_consumption_90[product.id][
                'total_consumption_90']
        return True

    @api.multi
    def calculate_average_days_dict(self, n_days):
        first_date = time.strftime('%Y-%m-%d')
        domain_move_out, begin_date, ctx = self.get_domain(self.ids, n_days)
        moves_out = self.env['stock.move'].read_group(
            domain_move_out, ['product_id', 'product_qty'], ['product_id'])
        moves_out = dict(map(lambda x: (x['product_id'][0], x['product_qty']),
                             moves_out))
        product_consumption = {}
        for product in self:
            product_consumption.setdefault(
                product.id,
                {}
            )
            qty_out = float_round(
                moves_out.get(product.id, 0.0),
                precision_rounding=product.uom_id.rounding)
            first_date = max(begin_date, product.with_context(ctx)._min_date())
            if n_days == 365:
                last_date = datetime.datetime.today()
                if ctx.get('force_from_date') and ctx.get('to_date'):
                    last_date = datetime.datetime.strptime(
                        ctx['to_date'], '%Y-%m-%d')
                nb_days = (
                    last_date -
                    datetime.datetime.strptime(first_date, '%Y-%m-%d')
                ).days or 1.0
                average_consumption = (
                    nb_days and qty_out / nb_days or 0.0)
                total_consumption = qty_out or 0.0
                if total_consumption == 0:
                    nb_days = 0.0
                else:
                    nb_days = nb_days or 0.0
                product_consumption[product.id]['nb_days'] = nb_days
                product_consumption[product.id]['average_consumption'] = (
                    average_consumption
                )
                product_consumption[product.id]['total_consumption'] = (
                    total_consumption
                )
            elif n_days == 15:
                average_consumption_15 = qty_out / 15 or 0.0
                total_consumption_15 = qty_out or 0.0
                product_consumption[product.id]['average_consumption_15'] = (
                    average_consumption_15
                )
                product_consumption[product.id]['total_consumption_15'] = (
                    total_consumption_15
                )
            elif n_days == 30:
                average_consumption_30 = qty_out / 30 or 0.0
                total_consumption_30 = qty_out or 0.0
                product_consumption[product.id]['average_consumption_30'] = (
                    average_consumption_30
                )
                product_consumption[product.id]['total_consumption_30'] = (
                    total_consumption_30
                )
            elif n_days == 90:
                average_consumption_90 = qty_out / 90 or 0.0
                total_consumption_90 = qty_out or 0.0
                product_consumption[product.id]['average_consumption_90'] = (
                    average_consumption_90
                )
                product_consumption[product.id]['total_consumption_90'] = (
                    total_consumption_90
                )
        return product_consumption

    def _get_domain_move_out_locations_average_consumption(
            self, avg_location_ids):
        warehouse_env = self.env['stock.warehouse']
        if self.env.context.get('company_owned', False):
            company_id = self.env.user.company_id.id
            return [
                ('location_id.company_id', '=', company_id),
                ('location_dest_id', 'in', avg_location_ids),
                ('location_dest_id.company_id', '=', company_id),
            ]
        location_ids = []
        if self.env.context.get('location', False):
            if isinstance(self.env.context['location'],
                          pycompat.integer_types):
                location_ids = [self.env.context['location']]
            elif isinstance(self.env.context['location'],
                            pycompat.string_types):
                domain = [
                    ('complete_name', 'ilike', self.env.context['location'])
                ]
                if self.env.context.get('force_company', False):
                    domain += [
                        ('company_id', '=', self.env.context['force_company'])
                    ]
                location_ids = self.env['stock.location'].search(domain).ids
            else:
                location_ids = self.env.context['location']
        else:
            if self.env.context.get('warehouse', False):
                if isinstance(self.env.context['warehouse'],
                              pycompat.integer_types):
                    wids = [self.env.context['warehouse']]
                elif isinstance(self.env.context['warehouse'],
                                pycompat.string_types):
                    domain = [('name', 'ilike', self.env.context['warehouse'])]
                    if self.env.context.get('force_company', False):
                        domain += [
                            ('company_id', '=', self.env.context[
                                'force_company'])
                        ]
                    wids = warehouse_env.search(domain).ids
                else:
                    wids = self.env.context['warehouse']
            else:
                wids = warehouse_env.search([]).ids

            for w in warehouse_env.browse(wids):
                location_ids.append(w.view_location_id.id)

        company_id = self.env.context.get('force_company', False)
        compute_child = self.env.context.get('compute_child', True)
        operator = compute_child and 'child_of' or 'in'
        domain = company_id and ['&', ('company_id', '=', company_id)] or []
        locations = self.env['stock.location'].browse(location_ids)
        hierarchical_locations = locations.filtered(
            lambda location: location.parent_left != 0
            and operator == "child_of")
        other_locations = locations.filtered(
            lambda location: location not in hierarchical_locations)
        loc_domain = []
        dest_loc_domain = [('location_dest_id', 'in', avg_location_ids)]
        if company_id:
            dest_loc_domain.append(
                ('location_dest_id.company_id', '=', company_id)
            )
        for location in hierarchical_locations:
            loc_domain = loc_domain and ['|'] + loc_domain or loc_domain
            loc_domain += [
                '&',
                ('location_id.parent_left', '>=', location.parent_left),
                ('location_id.parent_left', '<', location.parent_right)
            ]
        if other_locations:
            loc_domain = loc_domain and ['|'] + loc_domain or loc_domain
            loc_domain = loc_domain + [
                ('location_id', operator, [
                    location.id for location in other_locations])]
        return domain + loc_domain + dest_loc_domain

    @api.multi
    def _get_average_consumption_location_domain(self):
        company = self.env.user.company_id
        if company.product_average_consumption_location_ids:
            return self._get_domain_move_out_locations_average_consumption(
                company.product_average_consumption_location_ids.ids
            )
        domain_quant_loc, domain_move_in_loc, domain_move_out_loc = \
            self._get_domain_locations()
        return domain_move_out_loc

    @api.multi
    def _get_average_consumption_states_domain(self):
        company = self.env.user.company_id
        states = ('confirmed', 'waiting', 'assigned', 'done')
        if company.product_average_consumption_states:
            states = company.product_average_consumption_states.split(',')
        return [('state', 'in', states)]

    @api.multi
    def get_domain(self, product_ids, n_days):
        begin_date = (
            datetime.datetime.today() -
            datetime.timedelta(days=n_days)).strftime('%Y-%m-%d')
        ctx = dict(self.env.context)
        if ctx.get('from_date') and ctx.get('force_from_date'):
            begin_date = ctx['from_date']
        else:
            ctx.update({
                'from_date': begin_date
            })
        domain_products = [('product_id', 'in', product_ids)]
        domain_move_out = []
        domain_location = self._get_average_consumption_location_domain()
        domain_states = self._get_average_consumption_states_domain()
        domain_move_out += self._get_domain_dates(ctx) \
            + domain_states \
            + domain_products
        domain_move_out += domain_location
        return domain_move_out, begin_date, ctx

    def _get_domain_dates(self, context):
        from_date = context.get('from_date', False)
        to_date = context.get('to_date', False)
        domain = []
        if from_date:
            domain.append(('date', '>=', from_date))
        if to_date:
            domain.append(('date', '<=', to_date))
        return domain
