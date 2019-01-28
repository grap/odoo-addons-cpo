# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
# © 2018 FactorLibre - Álvaro Marcos <alvaro.marcos@factorlibre.com>
from openerp import models, fields


class ConsumptionRules(models.Model):
    _name = 'consumption.rules'

    initial_date = fields.Date('Initial date')
    end_date = fields.Date('End date')
    added_locations = fields.Many2many(
        'stock.location', string='Added locations to consumption')
    apply_to_calculation = fields.Boolean("Apply to calculation")
