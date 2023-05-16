# _*_ coding:utf-8_*_
import base64

from odoo import api, fields, models, _
import logging

from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class VehicleRepairWorkOrder(models.Model):
    _name = 'vehicle.repair.work.order'
    _inherit = ['portal.mixin', 'mail.thread', 'mail.activity.mixin']
    _description = "Vehicle Service Registration"
    _order = "id desc"

    name = fields.Char(string='Name', default="New", copy=False)
    customer_id = fields.Many2one('res.partner', 'Client', ondelete="restrict")
    date = fields.Datetime(string='Receiving Date', default=fields.Datetime.now)
    delivery_date = fields.Datetime(string='Delivery Date')
    phone = fields.Char(string='Phone', related="customer_id.phone", readonly=False)
    email = fields.Char(string="Email", related="customer_id.email", readonly=False)
    manager_ids = fields.Many2many('hr.employee', 'manager_repair_rel', 'manager_id', 'repair_id', string='Team Leader')
    repair_team_ids = fields.Many2many("vehicle.repair.team", string="Service Team")
    team_member_ids = fields.Many2many("hr.employee")
    plate_no = fields.Char(string='Plate Number')
    plate_exist = fields.Boolean()
    before_service_image_ids = fields.One2many('vehicle.service.image', 'registration_id2',
                                               string='Before Service Image')
    after_service_image_ids = fields.One2many('vehicle.service.image', 'registration_id', string='After Service Image')
    used_part_ids = fields.One2many('vehicle.part.used.info', 'repair_work_order_id')
    state = fields.Selection(
        [('draft', 'Draft'), ('confirm', 'Confirmed'), ('under_process', 'Under Process'),
         ('done', 'Done'), ('cancel', 'Canceled')], default='draft', copy=False, tracking=True)
    work_sheet_ids = fields.One2many('work.sheet', 'repair_work_order_id', string='Work Sheet')
    accomplished_date = fields.Datetime(string='Accomplished Date')
    vehicle_type_id = fields.Many2one("vehicle.vehicle.type", ondelete="restrict")
    brand_id = fields.Many2one("vehicle.brand", ondelete="restrict")
    issue_unknown = fields.Boolean()
    issue = fields.Text(string='Issue')
    service_template_id = fields.Many2one("vehicle.service.template")
    model = fields.Char(string='Model')
    color = fields.Char(string='Color')
    transmission_type = fields.Selection([("auto", "Automatic"), ("manual", "Manual")])
    last_oil_change_date = fields.Date("Last Change Oil")
    odometer_reading = fields.Float()
    fuel_value = fields.Integer(string='Fuel Level')
    fuel_gauge = fields.Integer(related="fuel_value")
    fuel_gauge_unit = fields.Char()
    fuel_type_id = fields.Many2one('fuel.type', string='Fuel Type', ondelete="restrict")
    year_of_manufacturing = fields.Char(string="Year of Manufacturing")
    warranty_date = fields.Boolean(string='Warranty')
    insurance = fields.Boolean(string='Insurance')
    pollution = fields.Boolean(string='Pollution')
    accessories_ids = fields.One2many('vehicle.accessories', 'repair_work_order_id',
                                      string='Accessories Available In Vehicle')
    sale_order_id = fields.Many2one("sale.order", string='Sale Oder Id', copy=False)
    currency_id = fields.Many2one("res.currency", default=lambda self: self.env.user.company_id.currency_id)
    work_sheet_expense = fields.Float(compute="compute_repair_expense", tracking=True, store=True)
    used_part_expense = fields.Float(compute="compute_repair_expense", tracking=True, store=True)
    total_repair_untaxed_expense = fields.Float(compute="compute_repair_expense", tracking=True,
                                                store=True)
    note = fields.Text(default="Total Final Amount may vary, this is a repair work order estimate.")
    priority = fields.Selection([('0', 'Very Low'), ('1', 'Low'), ('2', 'Normal'), ('3', 'High')], default='0',
                                string="Priority")
    active = fields.Boolean(default=True)

    @api.onchange("plate_no")
    def fetch_details_by_plate(self):
        if self.plate_no:
            plate_no = self.plate_no.replace(" ", "")
            self.plate_no = plate_no.upper()
            matched_vehicle_id = self.env["vehicle.detail.by.plate"].search([("plate_no", "=ilike", self.plate_no)],
                                                                            limit=1)
            if matched_vehicle_id:
                self.plate_exist = True
                self.customer_id = matched_vehicle_id.customer_id.id
                # self.phone = matched_vehicle_id.phone
                # self.email = matched_vehicle_id.email
                self.vehicle_type_id = matched_vehicle_id.vehicle_type_id.id
                self.brand_id = matched_vehicle_id.brand_id.id
                self.model = matched_vehicle_id.model
                self.color = matched_vehicle_id.color
                self.transmission_type = matched_vehicle_id.transmission_type
                self.fuel_type_id = matched_vehicle_id.fuel_type_id.id
                self.year_of_manufacturing = matched_vehicle_id.year_of_manufacturing
            else:
                self.plate_exist = False

    @api.depends("work_sheet_ids.subtotal", "used_part_ids.subtotal")
    def compute_repair_expense(self):
        for rec in self:
            if rec.work_sheet_ids:
                rec.work_sheet_expense = sum(rec.work_sheet_ids.mapped("subtotal"))
            else:
                rec.work_sheet_expense = 0
            if rec.used_part_ids:
                rec.used_part_expense = sum(rec.used_part_ids.mapped("subtotal"))
            rec.total_repair_untaxed_expense = rec.work_sheet_expense + rec.used_part_expense

    @api.onchange("service_template_id")
    def fill_from_template(self):
        service_template_id = self.service_template_id

        if service_template_id:
            self.repair_team_ids = service_template_id.repair_team_ids
            work_sheet = []
            for work_id in service_template_id.work_ids:
                work_sheet.append((0, 0, {
                    "mechanic_id": work_id.mechanic_id.id,
                    "service_id": work_id.service_id.id,
                    "description": work_id.description,
                    "cost_type": work_id.cost_type,
                    "cost": work_id.cost,
                    "abstract_uom": work_id.abstract_uom,
                    "qty": work_id.qty,
                    "time": work_id.time,
                }))
            self.work_sheet_ids = [(5, _, _)]
            self.work_sheet_ids = work_sheet
        else:
            self.work_sheet_ids = [(5, _, _)]

    @api.onchange("vehicle_type_id")
    def set_brand_domain(self):
        domain = {}
        if self.vehicle_type_id:
            domain.update({"brand_id": [('id', 'in', self.vehicle_type_id.vehicle_brand_ids.ids)]})
            domain.update({"service_template_id": [('vehicle_type_id', '=', self.vehicle_type_id.id)]})
        else:
            domain.update({"brand_id": []})
            domain.update({"service_template_id": []})

        return {"domain": domain}

    @api.onchange("brand_id")
    def set_template_domain(self):
        domain = {}
        if self.brand_id and self.vehicle_type_id:
            domain.update({"service_template_id": [('vehicle_type_id', '=', self.vehicle_type_id.id),
                                                   ('vehicle_brand_id', '=', self.brand_id.id)]})
        else:
            domain.update({"service_template_id": []})
        self.service_template_id = False
        return {"domain": domain}

    @api.onchange("repair_team_ids")
    def get_team_members(self):
        self.team_member_ids = False
        self.manager_ids = False
        if self.repair_team_ids:
            team_member_ids = self.repair_team_ids.mapped("team_member_ids")
            team_leader_id = self.repair_team_ids.mapped("team_leader_id")
            self.team_member_ids = team_member_ids.ids
            self.manager_ids = team_leader_id.ids
            work_sheet = self.env['work.sheet']
            if self.work_sheet_ids:
                for line in self.work_sheet_ids:
                    if line.mechanic_id.id not in team_member_ids.ids:
                        work_sheet += line
            if work_sheet:
                self.work_sheet_ids = [(2, x,) for x in work_sheet.ids]
        else:
            self.work_sheet_ids = False

    @api.model
    def create(self, vals):
        vals['name'] = self.env['ir.sequence'].get('vehicle.repair.work.order')
        res = super(VehicleRepairWorkOrder, self).create(vals)
        if res.plate_exist:
            matched_vehicle_id = self.env["vehicle.detail.by.plate"].search([("plate_no", "=ilike", res.plate_no)],
                                                                            limit=1)
            matched_vehicle_id.customer_id = res.customer_id.id
            matched_vehicle_id.phone = res.phone
            matched_vehicle_id.email = res.email
            matched_vehicle_id.vehicle_type_id = res.vehicle_type_id.id
            matched_vehicle_id.brand_id = res.brand_id.id
            matched_vehicle_id.model = res.model
            matched_vehicle_id.color = res.color
            matched_vehicle_id.transmission_type = res.transmission_type
            matched_vehicle_id.fuel_type_id = res.fuel_type_id.id
            matched_vehicle_id.year_of_manufacturing = res.year_of_manufacturing
        else:
            self.env["vehicle.detail.by.plate"].create({
                "plate_no": res.plate_no,
                "customer_id": res.customer_id.id,
                "phone": res.phone,
                "email": res.email,
                "vehicle_type_id": res.vehicle_type_id.id,
                "brand_id": res.brand_id.id,
                "model": res.model,
                "color": res.color,
                "transmission_type": res.transmission_type,
                "fuel_type_id": res.fuel_type_id.id,
                "year_of_manufacturing": res.year_of_manufacturing
            })
        return res

    def confirm_service(self):
        self.state = 'confirm'
        for repair_work_order in self.filtered(
                lambda work_order: work_order.customer_id not in work_order.message_partner_ids):
            repair_work_order.message_subscribe([repair_work_order.customer_id.id])

        self.send_email_user()

    def button_cancel(self):
        self.state = 'cancel'

    def button_draft(self):
        self.state = 'draft'

    def button_done(self):
        self.state = 'under_process'

    def button_finish(self):
        self.state = 'done'
        record_id = self.env['sale.order'].create({'partner_id': self.customer_id.id, 'order_line': self.order_line()})
        self.sale_order_id = record_id.id
        self.send_email_user()

    def order_line(self):
        res = []
        for work_line in self.work_sheet_ids:
            res.append((0, 0,
                        {
                            'product_id': work_line.service_id.product_id.id,
                            'name': work_line.description,
                            'price_unit': work_line.cost,
                            'product_uom_qty': work_line.qty
                        }))

        for used_part in self.used_part_ids:
            res.append((0, 0,
                        {
                            'product_id': used_part.part_id.id,
                            'name': used_part.description,
                            'product_uom_qty': used_part.quantity,
                        }))

        return res

    def sale_order_view(self):
        return {
            'type': 'ir.actions.act_window',
            'name': _('Sale Order'),
            'res_model': 'sale.order',
            'res_id': self.sale_order_id.id,
            'view_type': 'form',
            'view_mode': 'form',
            'target': 'current',
        }

    def send_email_user(self):
        res_data = self.env['ir.config_parameter'].sudo()
        send_email_confirm = res_data.get_param('vehical_repair_management.send_email_when_confirm', default=False)
        send_email_done = res_data.get_param('vehical_repair_management.send_email_when_done', default=False)
        send_email_to_customer = res_data.get_param('vehical_repair_management.send_email_when_customer_is_confirm',
                                                    default=False)

        if send_email_to_customer:
            html_body = "Dear Customer<br/>"
            html_body += "Your Vehicle Service Work Order Ref# " + str(
                self.name) + " is " + self.state + " and Vehicle Plate No is " + str(self.plate_no)
            html_body += "<br/>Check the attachment for more details.<br/><br/>Thanks<br/>Have a good day"
            self.send_email(html_body, self.customer_id)

        if send_email_confirm or send_email_done:
            user_ids = self.env.ref('vehical_repair_management.group_vehicle_repair_manager').users
            for user in user_ids:
                html_body = "Dear sir<br/>"
                html_body += "My vehicle Service Work Order Ref# " + str(
                    self.name) + " is " + self.state + " and Plate No is " + str(
                    self.plate_no) + "and fuel value  is " + str(self.fuel_value) + " and type is " + str(
                    self.fuel_type_id.name)
                if self.issue:
                    html_body += "<br/> Issue: <br/> " + str(self.issue)
                html_body += "<br/>Check the attachment for more details.<br/><br/>Thanks<br/>Have a good day"

                self.send_email(html_body, user)

    def send_email(self, html_body, user):
        pdf = self.env.ref('vehical_repair_management.action_report_drop_off_receipt')._render_qweb_pdf(self.id)[0]
        bounce_mail_values = {'body_html': html_body, 'subject': "Vehicle Service Work Order, Ref#: %s" % self.name,
                              'email_to': user.email, 'auto_delete': True, 'email_from': self.env.user.email_formatted,
                              'attachment_ids': [(0, 0, {
                                  'name': 'Vehicle Service Work Order %s' % self.name,
                                  'datas': base64.b64encode(pdf),
                                  'res_model': self._name,
                                  'res_id': self.id,
                                  'mimetype': 'application/pdf',
                                  'type': 'binary',
                                  'store_fname': 'Vehicle Service Work Order'
                              })]}

        self.env['mail.mail'].create(bounce_mail_values).send()

    def unlink(self):
        for rec in self:
            if rec.active and rec.state in ['confirm', 'under_process', 'done']:
                raise UserError(_('You cannot delete a confirmed, under process or done work order.'))
        return super(VehicleRepairWorkOrder, self).unlink()


class FuelType(models.Model):
    _name = 'fuel.type'

    name = fields.Char(string='Fuel Name')


class VehicleServiceImage(models.Model):
    _name = 'vehicle.service.image'

    image = fields.Binary(string='After Service')
    registration_id = fields.Many2one('vehicle.repair.work.order', string='After Service')
    registration_id2 = fields.Many2one('vehicle.repair.work.order', string='Before Service')


class WorkSheet(models.Model):
    _name = 'work.sheet'

    mechanic_id = fields.Many2one('hr.employee', string='Mechanic')
    description = fields.Text(string='Description')
    repair_work_order_id = fields.Many2one('vehicle.repair.work.order', string='Repair Work Order')
    service_id = fields.Many2one('vehicle.service', string='Service')
    cost = fields.Float(string='Price')
    cost_type = fields.Selection([("fix", "FIX"), ("price_varies", "PRICE VARIES"), ("free", "FREE")])
    abstract_uom = fields.Char()
    qty = fields.Float("Quantity", default=1)
    time = fields.Float('Work Time')
    subtotal = fields.Float(compute="compute_service_subtotal")
    currency_id = fields.Many2one("res.currency", related="repair_work_order_id.currency_id")
    sequence = fields.Integer()

    @api.depends("service_id", "cost", "qty")
    def compute_service_subtotal(self):
        for rec in self:
            if rec.cost and rec.qty:
                rec.subtotal = rec.cost * rec.qty
            else:
                rec.subtotal = 0

    @api.onchange("mechanic_id")
    def get_expertise_service(self):
        self.service_id = False
        if self.mechanic_id:
            expertise_service_ids = self.mechanic_id.expertise_service_ids
            vehicle_type_service_ids = self.repair_work_order_id.vehicle_type_id.service_ids
            common_services = set(expertise_service_ids.ids).intersection(vehicle_type_service_ids.ids)
            return {"domain": {
                "service_id": [("id", "in", list(common_services))]
            }}

    @api.onchange('service_id')
    def on_change_state(self):
        for record in self:
            if record.service_id:
                record.cost = record.service_id.cost
                record.description = record.service_id.description
                record.cost_type = record.service_id.cost_type
                if record.service_id.abstract_uom:
                    record.abstract_uom = "Per " + record.service_id.abstract_uom


class VehicleAccessories(models.Model):
    _name = 'vehicle.accessories'

    name = fields.Char(string='Name')
    quantity = fields.Integer(string='Quantity')
    description = fields.Text(string='Description')
    repair_work_order_id = fields.Many2one('vehicle.repair.work.order', string='Repair Work Order')


class ServiceInfo(models.Model):
    _name = 'vehicle.part.used.info'

    part_id = fields.Many2one('product.product', string='Part')
    description = fields.Text(string='Description')
    part_name = fields.Char(string='Part Name')
    part_no = fields.Char(string='Part #')
    quantity = fields.Integer(string='Qty', default='1')
    unit_price = fields.Float(string='Unit Price')
    subtotal = fields.Float(string='Subtotal')
    repair_work_order_id = fields.Many2one('vehicle.repair.work.order', string='Repair Work Order')
    currency_id = fields.Many2one("res.currency", related="repair_work_order_id.currency_id")

    @api.onchange('part_id')
    def _price_unit_change(self):
        self.unit_price = self.part_id.lst_price

    @api.onchange('quantity', 'unit_price')
    def _total_amount(self):
        self.subtotal = self.quantity * self.unit_price
