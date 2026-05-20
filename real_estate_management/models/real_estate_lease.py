from dateutil.relativedelta import relativedelta

from odoo import api, fields, models


class RealEstateLease(models.Model):
    _name = 'real.estate.lease'
    _description = 'Real Estate Lease'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'name desc'

    name = fields.Char(
        string='Lease Reference',
        readonly=True,
        copy=False,
        default='New',
    )
    unit_id = fields.Many2one(
        'real.estate.unit', string='Unit', required=True, tracking=True
    )
    building_id = fields.Many2one(
        'real.estate.building',
        string='Building',
        related='unit_id.building_id',
        store=True,
    )
    tenant_id = fields.Many2one(
        'res.partner', string='Tenant', required=True, tracking=True
    )
    start_date = fields.Date(string='Start Date', required=True, tracking=True)
    end_date = fields.Date(string='End Date', required=True, tracking=True)
    rent_amount = fields.Monetary(
        string='Monthly Rent', currency_field='currency_id', tracking=True
    )
    currency_id = fields.Many2one(
        'res.currency',
        string='Currency',
        default=lambda self: self.env.company.currency_id,
    )
    deposit_amount = fields.Monetary(
        string='Security Deposit', currency_field='currency_id'
    )
    state = fields.Selection(
        [
            ('draft', 'Draft'),
            ('active', 'Active'),
            ('expired', 'Expired'),
            ('cancelled', 'Cancelled'),
        ],
        string='State',
        default='draft',
        tracking=True,
    )
    next_invoice_date = fields.Date(string='Next Invoice Date')
    invoice_ids = fields.One2many(
        'account.move',
        'lease_id',
        string='Rent Invoices',
        domain=[('move_type', '=', 'out_invoice')],
    )
    invoice_count = fields.Integer(
        string='Invoices', compute='_compute_invoice_count'
    )
    utility_line_ids = fields.One2many(
        'real.estate.utility.line', 'lease_id', string='Utility Charges'
    )
    maintenance_ids = fields.One2many(
        'real.estate.maintenance', 'lease_id', string='Maintenance Requests'
    )
    maintenance_count = fields.Integer(
        string='Maintenance', compute='_compute_maintenance_count'
    )
    notes = fields.Text(string='Notes')

    @api.depends('invoice_ids')
    def _compute_invoice_count(self):
        for lease in self:
            lease.invoice_count = len(lease.invoice_ids)

    @api.depends('maintenance_ids')
    def _compute_maintenance_count(self):
        for lease in self:
            lease.maintenance_count = len(lease.maintenance_ids)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', 'New') == 'New':
                vals['name'] = self.env['ir.sequence'].next_by_code('real.estate.lease') or 'New'
        return super().create(vals_list)

    def action_activate(self):
        for lease in self:
            lease.state = 'active'
            lease.next_invoice_date = lease.start_date
            lease.unit_id.state = 'occupied'
            lease.unit_id.active_lease_id = lease

    def action_expire(self):
        for lease in self:
            lease.state = 'expired'
            lease.unit_id.state = 'available'
            lease.unit_id.active_lease_id = False

    def action_cancel(self):
        for lease in self:
            lease.state = 'cancelled'
            lease.unit_id.state = 'available'
            lease.unit_id.active_lease_id = False

    def action_generate_invoice(self):
        self.ensure_one()
        if not self.tenant_id:
            return False

        # Find income account (Odoo 19: account.account uses company_ids not company_id)
        income_account = self.env['account.account'].search(
            [('account_type', '=', 'income')],
            limit=1,
        )

        invoice_lines = []

        # Rent line
        invoice_lines.append(
            (
                0,
                0,
                {
                    'name': 'Rent - %s - %s'
                    % (
                        self.unit_id.name,
                        self.next_invoice_date.strftime('%B %Y') if self.next_invoice_date else '',
                    ),
                    'quantity': 1,
                    'price_unit': self.rent_amount,
                    'account_id': income_account.id if income_account else False,
                },
            )
        )

        # Pending utility lines for this lease
        pending_utilities = self.utility_line_ids.filtered(lambda u: u.state == 'pending')
        for util in pending_utilities:
            invoice_lines.append(
                (
                    0,
                    0,
                    {
                        'name': util.name or util.charge_type,
                        'quantity': 1,
                        'price_unit': util.amount,
                        'account_id': income_account.id if income_account else False,
                    },
                )
            )

        invoice_vals = {
            'move_type': 'out_invoice',
            'partner_id': self.tenant_id.id,
            'invoice_date': self.next_invoice_date or fields.Date.today(),
            'lease_id': self.id,
            'invoice_line_ids': invoice_lines,
        }

        invoice = self.env['account.move'].create(invoice_vals)

        # Mark utility lines as invoiced
        for i, util in enumerate(pending_utilities):
            # Find the corresponding invoice line
            if len(invoice.invoice_line_ids) > i + 1:
                util.invoice_line_id = invoice.invoice_line_ids[i + 1].id
            util.state = 'invoiced'

        # Advance next_invoice_date by 1 month
        if self.next_invoice_date:
            self.next_invoice_date = self.next_invoice_date + relativedelta(months=1)

        return True

    def action_view_invoices(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Invoices',
            'res_model': 'account.move',
            'view_mode': 'list,form',
            'domain': [('lease_id', '=', self.id), ('move_type', '=', 'out_invoice')],
            'context': {'default_lease_id': self.id, 'default_move_type': 'out_invoice'},
        }

    def action_view_maintenance(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Maintenance Requests',
            'res_model': 'real.estate.maintenance',
            'view_mode': 'list,form',
            'domain': [('lease_id', '=', self.id)],
            'context': {'default_lease_id': self.id},
        }

    @api.model
    def _generate_recurring_invoices(self):
        today = fields.Date.today()
        leases = self.search(
            [('state', '=', 'active'), ('next_invoice_date', '<=', today)]
        )
        for lease in leases:
            lease.action_generate_invoice()


class RealEstateUtilityLine(models.Model):
    _name = 'real.estate.utility.line'
    _description = 'Utility Charge Line'
    _order = 'date desc'

    lease_id = fields.Many2one(
        'real.estate.lease', string='Lease', required=True, ondelete='cascade'
    )
    name = fields.Char(string='Description')
    charge_type = fields.Selection(
        [
            ('electricity', 'Electricity'),
            ('water', 'Water'),
            ('gas', 'Gas'),
            ('internet', 'Internet'),
            ('other', 'Other'),
        ],
        string='Charge Type',
        required=True,
    )
    amount = fields.Monetary(string='Amount', currency_field='currency_id')
    currency_id = fields.Many2one(
        'res.currency',
        string='Currency',
        related='lease_id.currency_id',
    )
    date = fields.Date(string='Date', default=fields.Date.today)
    state = fields.Selection(
        [('pending', 'Pending'), ('invoiced', 'Invoiced')],
        string='State',
        default='pending',
    )
    invoice_line_id = fields.Many2one('account.move.line', string='Invoice Line')
