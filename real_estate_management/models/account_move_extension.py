from odoo import fields, models


class AccountMove(models.Model):
    _inherit = 'account.move'

    lease_id = fields.Many2one(
        'real.estate.lease',
        string='Lease',
        ondelete='set null',
        index=True,
    )
