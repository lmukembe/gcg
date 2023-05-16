# _*_ coding:utf-8_*_

from odoo import api, fields, models, _

import logging

_logger = logging.getLogger(__name__)


class VehicleService(models.Model):
    _name = 'vehicle.service'

    name = fields.Char(string="Name")
    product_id = fields.Many2one('product.product', string='Product', ondelete="restrict")
    cost_type = fields.Selection([("fix", "FIX"), ("price_varies", "PRICE VARIES"), ("free", "FREE")], default='fix',
                                 required=True)
    cost = fields.Float(string="Price", digits='Product Price')
    abstract_uom = fields.Char()
    currency_id = fields.Many2one("res.currency", default=lambda self: self.env.user.company_id.currency_id)
    description = fields.Text(string="Description")
    service_type_id = fields.Many2one('service.type', string='Service Category', ondelete="restrict")
    service_for_vehicle_type_ids = fields.Many2many("vehicle.vehicle.type", "vehicle_service_vehicle_type_rel",
                                                    "vehicle_type_id", "service_id")

    @api.onchange("cost_type", "product_id")
    def set_cost(self):
        if self.cost_type == "free":
            self.cost = 0
        elif self.cost_type in ["fix", "price_varies"]:
            self.cost = self.product_id and self.product_id.lst_price


class ServiceType(models.Model):
    _name = 'service.type'

    name = fields.Char(string="Service Category")


class VehicleProduct(models.Model):
    _inherit = 'product.product'

    is_part = fields.Boolean(string="Is Vehicle Part")


class VehicleSetting(models.TransientModel):
    _inherit = 'res.config.settings'

    send_email_when_confirm = fields.Boolean("Manager: Send Confirmation Mail")
    send_email_when_done = fields.Boolean(string='Manager: Send Done Mail')
    send_email_when_customer_is_confirm = fields.Boolean('Customer: Send Confirmation & Done Mail')

    @api.model
    def get_values(self):
        res = super(VehicleSetting, self).get_values()
        res_data = self.env['ir.config_parameter'].sudo()

        res.update(
            send_email_when_confirm=res_data.get_param('vehical_repair_management.send_email_when_confirm',
                                                       default=False),
            send_email_when_done=res_data.get_param('vehical_repair_management.send_email_when_done', default=False),
            send_email_when_customer_is_confirm=res_data.get_param(
                'vehical_repair_management.send_email_when_customer_is_confirm', default=False),
        )
        return res

    def set_values(self):
        super(VehicleSetting, self).set_values()
        res_data = self.env['ir.config_parameter'].sudo()

        res_data.set_param("vehical_repair_management.send_email_when_confirm", self.send_email_when_confirm)
        res_data.set_param("vehical_repair_management.send_email_when_done", self.send_email_when_done)
        res_data.set_param("vehical_repair_management.send_email_when_customer_is_confirm",
                           self.send_email_when_customer_is_confirm)


class RepairTeam(models.Model):
    _name = "vehicle.repair.team"
    _description = "Vehicle Repair Team"

    name = fields.Char("Team Name", required=True)
    team_logo = fields.Binary()
    team_leader_id = fields.Many2one("hr.employee", required=True, ondelete="restrict")
    team_description = fields.Text()
    team_member_ids = fields.Many2many("hr.employee", "hr_emp_repair_team_rel", "emp_id", "team_id",
                                       domain=[("is_mechanic", "=", True)],  ondelete="restrict")
    vehicle_service_ids = fields.Many2many("vehicle.service", required=True,  ondelete="restrict")

    @api.onchange("team_leader_id", "vehicle_service_ids")
    def filter_employees(self):
        domain = [("is_mechanic", "=", True)]
        if self.vehicle_service_ids:
            domain.append(("expertise_service_ids", "in", self.vehicle_service_ids.ids))
        if self.team_leader_id:
            domain.append(("parent_id", "=", self.team_leader_id.id))

        emp_ids = self.env["hr.employee"].search(domain)
        return {"domain": {'team_member_ids': [('id', 'in', emp_ids.ids)]}}


class HrEmployee(models.Model):
    _inherit = "hr.employee"

    is_mechanic = fields.Boolean(string="Is Mechanic")
    expertise_service_ids = fields.Many2many("vehicle.service",  ondelete="restrict")
    repair_team_ids = fields.Many2many("vehicle.repair.team", "hr_emp_repair_team_rel", "team_id", "emp_id")

    def name_get(self):
        res = []
        for record in self:
            if record.is_mechanic:
                name = record.name + " (" + ",".join(record.repair_team_ids.mapped("name")) + ")"
                res.append((record.id, name))
            else:
                name = record.name
                res.append((record.id, name))
        return res


class VehicleType(models.Model):
    _name = "vehicle.vehicle.type"

    name = fields.Char()
    vehicle_brand_ids = fields.Many2many("vehicle.brand", "vehicle_type_brand_rel", "vehicle_brand_id",
                                         "vehicle_type_id", string="Vehicle Brands",  ondelete="restrict")
    service_ids = fields.Many2many("vehicle.service", "vehicle_service_vehicle_type_rel",
                                   "service_id", "vehicle_type_id",  ondelete="restrict")


class VehicleBrand(models.Model):
    _name = "vehicle.brand"

    name = fields.Char()
    image = fields.Binary()
    mfg_vehicle_type_ids = fields.Many2many("vehicle.vehicle.type", "vehicle_type_brand_rel", "vehicle_type_id",
                                            "vehicle_brand_id", string="Manufactured Vehicle Types")


class VehicleServiceTemplate(models.Model):
    _name = "vehicle.service.template"

    name = fields.Char()
    vehicle_type_id = fields.Many2one("vehicle.vehicle.type")
    vehicle_brand_id = fields.Many2one("vehicle.brand")
    repair_team_ids = fields.Many2many("vehicle.repair.team")
    team_member_ids = fields.Many2many("hr.employee")
    work_ids = fields.One2many("vehicle.service.work.line", "service_template_id")
    active = fields.Boolean(default=True)
    currency_id = fields.Many2one("res.currency", default=lambda self: self.env.user.company_id.currency_id)

    @api.onchange("vehicle_type_id")
    def set_brand_domain(self):
        if self.vehicle_type_id:
            return {"domain": {"vehicle_brand_id": [('id', 'in', self.vehicle_type_id.vehicle_brand_ids.ids)]}}

    @api.onchange("repair_team_ids")
    def get_team_members(self):
        self.team_member_ids = False
        if self.repair_team_ids:
            team_member_ids = self.repair_team_ids.mapped("team_member_ids")
            print("team_member_ids", team_member_ids)
            self.team_member_ids = team_member_ids.ids
            work_sheet = self.env['vehicle.service.work.line']
            if self.work_ids:
                for line in self.work_ids:
                    if line.mechanic_id.id not in team_member_ids.ids:
                        work_sheet += line
            if work_sheet:
                self.work_ids = [(2, x,) for x in work_sheet.ids]
        else:
            self.work_ids = False


class VehicleServiceWorkLine(models.Model):
    _name = "vehicle.service.work.line"

    service_template_id = fields.Many2one("vehicle.service.template")
    mechanic_id = fields.Many2one('hr.employee', string='Mechanic', ondelete="restrict")
    service_id = fields.Many2one('vehicle.service', string='Service', ondelete="restrict")
    description = fields.Text(string='Description')
    cost_type = fields.Selection([("fix", "FIX"), ("price_varies", "PRICE VARIES"), ("free", "FREE")], required=True)
    cost = fields.Float(string='Cost')
    abstract_uom = fields.Char()
    qty = fields.Float("Quantity", default=1)
    time = fields.Float('Work Time')
    subtotal = fields.Float(compute="compute_service_subtotal")
    sequence = fields.Integer()
    currency_id = fields.Many2one("res.currency", related="service_template_id.currency_id")

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
            vehicle_type_service_ids = self.service_template_id.vehicle_type_id.service_ids
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


class VehicleByPlate(models.Model):
    _name = "vehicle.detail.by.plate"
    _rec_name = "plate_no"

    plate_no = fields.Char(string='Plate No')
    customer_id = fields.Many2one('res.partner', 'Customer')
    phone = fields.Char(string='Phone', related="customer_id.phone", readonly=False)
    email = fields.Char(string="Email", related="customer_id.email", readonly=False)
    vehicle_type_id = fields.Many2one("vehicle.vehicle.type", ondelete="restrict")
    brand_id = fields.Many2one("vehicle.brand", ondelete="restrict")
    model = fields.Char(string='Model')
    color = fields.Char(string='Color')
    transmission_type = fields.Selection([("auto", "Automatic"), ("manual", "Manual")])
    fuel_type_id = fields.Many2one('fuel.type', string='Fuel Type', ondelete="restrict")
    year_of_manufacturing = fields.Char(string="Year of Manufacturing")

    @api.onchange("plate_no")
    def fetch_details_by_plate(self):
        if self.plate_no:
            plate_no = self.plate_no.replace(" ", "")
            self.plate_no = plate_no.upper()
