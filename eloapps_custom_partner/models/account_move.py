# -*- encoding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError
import logging as log

class AccountMove(models.Model):
    _inherit = 'account.move'

    @api.model
    def get_domain(self):
        type_inv = self._context.get('default_move_type', 'entry')
        if type_inv in ('out_invoice', 'out_refund', 'out_receipt'):
            return [('customer', '=', True)]
        elif type_inv in ('in_invoice', 'in_refund', 'in_receipt'):
            return [('supplier', '=', True)]

    partner_id = fields.Many2one(
        'res.partner',
        readonly=True,
        tracking=True,
        states={'draft': [('readonly', False)]},
        domain=get_domain,
        string='Partner',
        change_default=True
    )