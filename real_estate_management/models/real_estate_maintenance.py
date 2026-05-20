from odoo import api, fields, models


class RealEstateMaintenance(models.Model):
    _name = 'real.estate.maintenance'
    _description = 'Real Estate Maintenance Request'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'date_reported desc'

    name = fields.Char(string='Subject', required=True, tracking=True)
    sequence = fields.Char(
        string='Reference', readonly=True, copy=False, default='New'
    )
    # Building first — filters available units below
    building_id = fields.Many2one(
        'real.estate.building', string='Building', tracking=True
    )
    unit_id = fields.Many2one(
        'real.estate.unit', string='Unit', required=True, tracking=True
    )
    lease_id = fields.Many2one('real.estate.lease', string='Lease')
    tenant_id = fields.Many2one(
        'res.partner',
        string='Tenant',
        related='lease_id.tenant_id',
        store=True,
    )
    description = fields.Text(string='Description')
    date_reported = fields.Date(
        string='Date Reported', default=fields.Date.today
    )
    date_resolved = fields.Date(string='Date Resolved')
    priority = fields.Selection(
        [
            ('normal', 'Normal'),
            ('urgent', 'Urgent'),
            ('very_urgent', 'Very Urgent'),
        ],
        string='Priority',
        default='normal',
        tracking=True,
    )
    state = fields.Selection(
        [
            ('new', 'New'),
            ('in_progress', 'In Progress'),
            ('done', 'Done'),
            ('cancelled', 'Cancelled'),
        ],
        string='State',
        default='new',
        tracking=True,
    )
    vendor_id = fields.Many2one(
        'res.partner', string='Vendor', tracking=True
    )
    cost = fields.Monetary(string='Cost', currency_field='currency_id')
    currency_id = fields.Many2one(
        'res.currency',
        string='Currency',
        default=lambda self: self.env.company.currency_id,
    )
    bill_id = fields.Many2one('account.move', string='Vendor Bill')
    bill_count = fields.Integer(string='Bills', compute='_compute_bill_count')
    notes = fields.Text(string='Notes')

    # ── onchange cascades ──────────────────────────────────────────────────

    @api.onchange('building_id')
    def _onchange_building_id(self):
        """When building changes, clear unit and lease if they no longer match."""
        if self.unit_id and self.unit_id.building_id != self.building_id:
            self.unit_id = False
            self.lease_id = False

    @api.onchange('unit_id')
    def _onchange_unit_id(self):
        """Auto-fill building and active lease when a unit is chosen."""
        if self.unit_id:
            self.building_id = self.unit_id.building_id
            self.lease_id = self.unit_id.active_lease_id or False
        else:
            self.lease_id = False

    # ── computes ───────────────────────────────────────────────────────────

    @api.depends('bill_id')
    def _compute_bill_count(self):
        for rec in self:
            rec.bill_count = 1 if rec.bill_id else 0

    # ── ORM overrides ──────────────────────────────────────────────────────

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            # Auto-fill building_id from unit when not provided
            if vals.get('unit_id') and not vals.get('building_id'):
                unit = self.env['real.estate.unit'].browse(vals['unit_id'])
                vals['building_id'] = unit.building_id.id or False
            if vals.get('sequence', 'New') == 'New':
                vals['sequence'] = (
                    self.env['ir.sequence'].next_by_code('real.estate.maintenance') or 'New'
                )
        return super().create(vals_list)

    # ── actions ────────────────────────────────────────────────────────────

    def action_start(self):
        self.state = 'in_progress'

    def action_done(self):
        self.state = 'done'
        self.date_resolved = fields.Date.today()

    def action_cancel(self):
        self.state = 'cancelled'

    def action_create_bill(self):
        self.ensure_one()
        if not self.vendor_id:
            return False

        expense_account = self.env['account.account'].search(
            [('account_type', '=', 'expense')],
            limit=1,
        )

        bill_vals = {
            'move_type': 'in_invoice',
            'partner_id': self.vendor_id.id,
            'invoice_date': fields.Date.today(),
            'invoice_line_ids': [
                (
                    0,
                    0,
                    {
                        'name': self.name,
                        'quantity': 1,
                        'price_unit': self.cost,
                        'account_id': expense_account.id if expense_account else False,
                    },
                )
            ],
        }

        bill = self.env['account.move'].create(bill_vals)
        self.bill_id = bill.id
        return True

    def action_view_bill(self):
        self.ensure_one()
        if not self.bill_id:
            return False
        return {
            'type': 'ir.actions.act_window',
            'name': 'Vendor Bill',
            'res_model': 'account.move',
            'view_mode': 'form',
            'res_id': self.bill_id.id,
        }
