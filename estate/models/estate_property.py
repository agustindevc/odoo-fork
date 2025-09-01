# Modelo principal para propiedades inmobiliarias en la app estate

from odoo import models, fields, api
from datetime import date
from dateutil.relativedelta import relativedelta
from odoo.exceptions import UserError, ValidationError
from odoo.tools.float_utils import float_compare, float_is_zero

class EstateProperty(models.Model):
    # Título de la propiedad
    _name = 'estate.property'
    _description = 'Property'
    _order = "id desc"

    name = fields.Char(string='Title', required=True)
    
    # Código postal
    postcode = fields.Char(string='Postcode')
    
    # Fecha en la que la propiedad estará disponible
    date_availability = fields.Date(
        string='Date Availability',
        copy=False,
        default=lambda self: date.today() + relativedelta(months=3)
    )
   
    # Precio esperado de venta
    expected_price = fields.Float(string='Expected Price', required=True)
    
    # Precio final de venta (solo lectura)
    selling_price = fields.Float(string='Selling Price', readonly=True, copy=False)
    
    # Número de dormitorios
    bedrooms = fields.Integer(string='Bedrooms', default=2)
    
    # Superficie habitable
    living_area = fields.Float(string='Living Area (sqm)')
    
    # Número de fachadas
    facades = fields.Integer(string='Facades')
    
    # Tiene garaje?
    garage = fields.Boolean(string='Garage')
    
    # Activa o archivada
    active = fields.Boolean(string="Active", default=True)
    
    # Estado de la propiedad
    state = fields.Selection([
        ('new', 'New'),
        ('offer_received', 'Offer Received'),
        ('offer_accepted', 'Offer Accepted'),
        ('sold', 'Sold'),
        ('canceled', 'Canceled'),
    ], string='Status', required=True, copy=False, default='new')
    
    # Tiene jardín?
    garden = fields.Boolean(string='Garden')
    
    # Superficie del jardín
    garden_area = fields.Integer(string='Garden Area (sqm)')
    
    # Orientación del jardín
    garden_orientation = fields.Selection([
        ('north', 'North'),
        ('south', 'South'),
        ('east', 'East'),
        ('west', 'West'),
    ], string='Garden Orientation')
    
    # Usuario vendedor
    seller_id = fields.Many2one(
        'res.users',
        string="Seller",
        default=lambda self: self.env.user
    )
    
    # Comprador (si se vendió)
    buyer_id = fields.Many2one(
        'res.partner',
        string="Buyer",
        copy=False
    )
    
    # Tipo de propiedad
    property_type_id = fields.Many2one(
        'estate.property.type',
        string='Property Type'
    )
    
    # Etiquetas asociadas a una propiedad
    tag_ids = fields.Many2many(
        "estate.property.tag",
        "estate_property_tag_rel",
        "property_id",             
        string="Tags"
    )
    
    # Ofertas realizadas sobre esta propiedad
    offer_ids = fields.One2many(
        "estate.property.offer",
        "property_id",
        string="Offers"
    )
    
    # Superficie total (habitable + jardín)
    total_area = fields.Float(
        string="Total Area (sqm)",
        compute="_compute_total_area",
        store=True
    )
    
    # Mejor oferta recibida
    best_offer = fields.Float(
        string="Best Offer",
        compute="_compute_best_offer",
        store=True
    )
    
    # Calcula la superficie total
    @api.depends("living_area", "garden_area")
    def _compute_total_area(self):
        for record in self:
            record.total_area = (record.living_area or 0.0) + (record.garden_area or 0.0)
    
    # Calcula la mejor oferta recibida
    @api.depends("offer_ids.price")
    def _compute_best_offer(self):
        for record in self:
            prices = record.offer_ids.mapped("price")
            record.best_offer = max(prices) if prices else 0.0

    # Al marcar/desmarcar jardín, asigna valores por defecto
    @api.onchange('garden')
    def _onchange_garden(self):
        if self.garden:
            self.garden_area = 10
            self.garden_orientation = 'north'
        else:
            self.garden_area = 0
            self.garden_orientation = False
            
    # Cancela la propiedad si no está vendida
    def action_cancel(self):
        for record in self:
            if record.state == 'sold':
                raise UserError("No se puede cancelar una propiedad ya vendida.")
            record.state = 'canceled'
        return True
    
    # Marca la propiedad como vendida si no está cancelada
    def action_mark_sold(self):
        for record in self:
            if record.state == 'canceled':
                raise UserError("No se puede vender una propiedad cancelada.")
            record.state = 'sold'
        return True
    
    # Restricciones SQL para precios válidos    
    _sql_constraints = [
        ('check_expected_price_positive',
         'CHECK(expected_price > 0)',
         'The expected price must be strictly positive.'),
        ('check_selling_price_positive',
         'CHECK(selling_price >= 0)',
         'The selling price must be positive.')
    ]
    
    # Valida que el precio de venta no sea menor al 90% del esperado
    @api.constrains("expected_price", "selling_price")
    def _check_selling_price(self):
        for record in self:
            if float_is_zero(record.selling_price, precision_digits=2):
                continue

            min_acceptable_price = record.expected_price * 0.9
            if float_compare(record.selling_price, min_acceptable_price, precision_digits=2) < 0:
                raise ValidationError(
                    "El precio de venta no puede ser inferior al 90% del precio esperado."
                )
    
    # Indica si la mejor oferta fue aceptada
    best_offer_accepted = fields.Boolean(
        string="Best Offer Accepted",
        compute="_compute_best_offer_accepted"
    )
    
    # Calcula si la mejor oferta está aceptada
    @api.depends("offer_ids.status")
    def _compute_best_offer_accepted(self):
        for record in self:
            best_price = record.best_offer
            record.best_offer_accepted = any(
                offer.price == best_price and offer.status == 'accepted'
                for offer in record.offer_ids
            )
    
    # Booleanos para mostrar el estado de la propiedad en la interfaz
    offer_received_bool = fields.Boolean(
        string="Oferta recibida",
        compute="_compute_offer_flags",
        store=True
    )
    offer_accepted_bool = fields.Boolean(
        string="Oferta aceptada",
        compute="_compute_offer_flags",
        store=True
    )
    sold_bool = fields.Boolean(
        string="Vendida",
        compute="_compute_offer_flags",
        store=True
    )
    
    # Calcula los indicadores booleanos de estado para la interfaz
    @api.depends('offer_ids.status', 'state')
    def _compute_offer_flags(self):
        for prop in self:
            prop.sold_bool = prop.state in ['sold', 'canceled']

            if not prop.sold_bool:
                prop.offer_received_bool = bool(prop.offer_ids)
                prop.offer_accepted_bool = any(prop.offer_ids.filtered(lambda o: o.status == 'accepted'))
            else:
                prop.offer_received_bool = False
                prop.offer_accepted_bool = False
    
    # Solo permite eliminar propiedades nuevas o canceladas
    def unlink(self):
        for record in self:
            if record.state not in ['new', 'canceled']:
                raise UserError("Solo se pueden eliminar propiedades en estado 'Nueva' o 'Cancelada'.")
        return super(EstateProperty, self).unlink()
