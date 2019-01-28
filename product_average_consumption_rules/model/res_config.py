# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
# © 2018 FactorLibre - Álvaro Marcos <alvaro.marcos@factorlibre.com>

from openerp import api, models, fields


class ResConfig(models.TransientModel):

    _inherit = 'res.config.settings'

    initial_date = fields.Date('Initial date')
    end_date = fields.Date('End date')
    added_locations = fields.Many2many(
        'stock.location', string='Added locations to consumption')
    apply_to_calculation = fields.Boolean("Apply to calculation")

    @api.multi
    def set_values(self):
        super(ResConfig, self).set_values()
        Sudo = self.env['ir.config_parameter'].sudo()
        Sudo.set_param('initial_date', self.initial_date)
        Sudo.set_param('end_date', self.end_date)
        Sudo.set_param('added_locations', self.added_locations.ids)
        Sudo.set_param('apply_to_calculation', self.apply_to_calculation)

    @api.model
    def get_values(self):
        res = super(ResConfig, self).get_values()
        Sudo = self.env['ir.config_parameter'].sudo()
        initial_date = Sudo.get_param('initial_date')
        end_date = Sudo.get_param('end_date')
        end_date = Sudo.get_param('end_date')
        added_locations = Sudo.get_param('added_locations')
        apply_to_calculation = Sudo.get_param('apply_to_calculation')
        res.update({
            'initial_date': initial_date,
            'end_date': end_date,
            'added_locations': [(6, 0, added_locations)],
            'apply_to_calculation': apply_to_calculation
        })
        return res
