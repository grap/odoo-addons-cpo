# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
# © 2018 FactorLibre - Álvaro Marcos <alvaro.marcos@factorlibre.com>
import datetime
from openerp import models, api


class ProductProduct(models.Model):
    _inherit = "product.product"

    @api.multi
    def get_domain(self, product_ids, n_days):
        super(ProductProduct, self).get_domain(product_ids, n_days)
        begin_date = (
            datetime.datetime.today() -
            datetime.timedelta(days=n_days)).strftime('%Y-%m-%d')
        ctx = dict(self.env.context)
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
        rules = self.env['consumption.rules'].search([
            ('apply_to_calculation', '=', True)
        ], limit=1)
        if rules:
            location_ids = rules.added_locations.ids
            alternate_domain = ['|', '&', ('location_id', 'in', location_ids),
                                '&', ('date', '>=', rules.initial_date),
                                ('date', '<', rules.end_date), '&']
            domain_move_out += alternate_domain
        domain_move_out += domain_location
        return domain_move_out, begin_date, ctx

    # Prototipo para calculo con fehcas mayores a 365
    # @api.multi
    # def get_domain(self, product_ids, n_days):
    #     super(ProductProduct, self).get_domain(product_ids, n_days)
    #     begin_date = (
    #         datetime.datetime.today() -
    #         datetime.timedelta(days=n_days)).strftime('%Y-%m-%d')
    #     ctx = dict(self.env.context)
    #     ctx.update({
    #         'from_date': begin_date
    #     })
    #     domain_products = [('product_id', 'in', product_ids)]
    #     domain_move_out = []
    #     domain_quant_loc, domain_move_in_loc, domain_move_out_loc = \
    #         self._get_domain_locations()
    #     domain_move_out += self._get_domain_dates(ctx) \
    #         + [('state', 'in', ('confirmed', 'waiting', 'assigned', 'done'))] \
    #         + domain_products
    #     rules = self.env['consumption.rules'].search([
    #         ('apply_to_calculation', '=', True)
    #     ], limit=1)
    #     domain_move_out_extra = []
    #     if rules:
    #         location_ids = rules.added_locations.ids
    #         domain_move_out_extra = [('location_id', 'in', location_ids),
    #                                  ('date', '>=', rules.initial_date),
    #                                  ('date', '<', rules.end_date)
    #                                 ] + domain_products + ['!'] + domain_move_out_loc
    #     domain_move_out += domain_move_out_loc
    #     return domain_move_out, domain_move_out_extra, begin_date, ctx
