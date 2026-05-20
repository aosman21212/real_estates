from odoo import api, fields, models


class RealEstateBuilding(models.Model):
    _name = 'real.estate.building'
    _description = 'Real Estate Building'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'name'

    name = fields.Char(string='Building Name', required=True, tracking=True)
    street = fields.Char(string='Street')
    city = fields.Char(string='City', tracking=True)
    zip = fields.Char(string='ZIP')
    country_id = fields.Many2one('res.country', string='Country')
    owner_id = fields.Many2one('res.partner', string='Owner', tracking=True)
    unit_ids = fields.One2many('real.estate.unit', 'building_id', string='Units')
    maintenance_ids = fields.One2many('real.estate.maintenance', 'building_id', string='Maintenance Requests')
    notes = fields.Text(string='Notes')

    total_units = fields.Integer(
        string='Total Units',
        compute='_compute_unit_stats',
        store=True,
    )
    occupied_units = fields.Integer(
        string='Occupied Units',
        compute='_compute_unit_stats',
        store=True,
    )
    available_units = fields.Integer(
        string='Available Units',
        compute='_compute_unit_stats',
        store=True,
    )
    maintenance_count = fields.Integer(
        string='Maintenance',
        compute='_compute_maintenance_count',
    )

    @api.depends('unit_ids', 'unit_ids.state')
    def _compute_unit_stats(self):
        for building in self:
            units = building.unit_ids
            building.total_units = len(units)
            building.occupied_units = len(units.filtered(lambda u: u.state == 'occupied'))
            building.available_units = len(units.filtered(lambda u: u.state == 'available'))

    def _compute_maintenance_count(self):
        data = self.env['real.estate.maintenance'].read_group(
            [('building_id', 'in', self.ids)],
            ['building_id'],
            ['building_id'],
        )
        count_map = {d['building_id'][0]: d['building_id_count'] for d in data}
        for building in self:
            building.maintenance_count = count_map.get(building.id, 0)

    def action_view_maintenance(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Maintenance Requests',
            'res_model': 'real.estate.maintenance',
            'view_mode': 'list,kanban,form',
            'domain': [('building_id', '=', self.id)],
            'context': {'default_building_id': self.id},
        }
