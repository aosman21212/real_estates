from odoo import api, fields, models


class RealEstateUnit(models.Model):
    _name = 'real.estate.unit'
    _description = 'Real Estate Unit'
    _inherit = ['mail.thread']
    _order = 'building_id, name'

    name = fields.Char(string='Unit Number', required=True, tracking=True)
    building_id = fields.Many2one(
        'real.estate.building', string='Building', required=True, ondelete='cascade', tracking=True
    )
    floor = fields.Integer(string='Floor')
    area = fields.Float(string='Area (sqm)')
    bedrooms = fields.Integer(string='Bedrooms')
    bathrooms = fields.Integer(string='Bathrooms')
    rent_amount = fields.Monetary(string='Monthly Rent', currency_field='currency_id', tracking=True)
    currency_id = fields.Many2one(
        'res.currency',
        string='Currency',
        default=lambda self: self.env.company.currency_id,
    )
    state = fields.Selection(
        [
            ('available', 'Available'),
            ('occupied', 'Occupied'),
            ('maintenance', 'Maintenance'),
        ],
        string='State',
        default='available',
        tracking=True,
    )
    notes = fields.Text(string='Notes')

    active_lease_id = fields.Many2one(
        'real.estate.lease',
        string='Active Lease',
        readonly=True,
        copy=False,
    )
    tenant_id = fields.Many2one(
        'res.partner',
        string='Current Tenant',
        related='active_lease_id.tenant_id',
        store=True,
    )
    maintenance_count = fields.Integer(
        string='Maintenance',
        compute='_compute_maintenance_count',
    )

    def _compute_maintenance_count(self):
        data = self.env['real.estate.maintenance'].read_group(
            [('unit_id', 'in', self.ids)],
            ['unit_id'],
            ['unit_id'],
        )
        count_map = {d['unit_id'][0]: d['unit_id_count'] for d in data}
        for unit in self:
            unit.maintenance_count = count_map.get(unit.id, 0)

    def action_view_maintenance(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Maintenance Requests',
            'res_model': 'real.estate.maintenance',
            'view_mode': 'list,kanban,form',
            'domain': [('unit_id', '=', self.id)],
            'context': {
                'default_unit_id': self.id,
                'default_building_id': self.building_id.id,
            },
        }
