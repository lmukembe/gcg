# -*- encoding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError

class ResPartner(models.Model):
    _inherit = 'res.partner'

    def default_customer(self):
        customer = self.env.context.get('res_partner_search_mode') == 'customer'
        supplier = self.env.context.get('res_partner_search_mode') == 'supplier'
        if customer or (not customer and not supplier):
            return True
        return False

    def default_supplier(self):
        supplier = self.env.context.get('res_partner_search_mode') == 'supplier'
        if supplier:
            return True
        return False

    customer = fields.Boolean(
        string='Is a Customer',
        default=lambda self: self.default_customer(),
        help="Check this box if this contact is a customer. It can be selected in sales orders."
    )

    supplier = fields.Boolean(
        string='Is a Vendor',
        default=lambda self: self.default_supplier(),
        help="Check this box if this contact is a vendor. It can be selected in purchase orders."
    )

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if 'customer' in vals:
                vals['customer_rank'] = int(vals.get('customer'))
            if 'supplier' in vals:
                vals['supplier_rank'] = int(vals.get('supplier'))

            if 'customer_rank' in vals:
                vals['customer'] = bool(vals.get('customer_rank'))
            if 'supplier_rank' in vals:
                vals['supplier'] = bool(vals.get('supplier_rank'))
        return super(ResPartner, self).create(vals_list)

    def write(self, vals):
        if 'customer' in vals:
            vals['customer_rank'] = int(vals.get('customer'))
        if 'supplier' in vals:
            vals['supplier_rank'] = int(vals.get('supplier'))

        if 'customer_rank' in vals:
            vals['customer'] = bool(vals.get('customer_rank'))
        if 'supplier_rank' in vals:
            vals['supplier'] = bool(vals.get('supplier_rank'))

        return super(ResPartner, self).write(vals)
