from datetime import timedelta
from odoo import api, models, fields
from odoo.exceptions import UserError

# Modelo para ofertas de propiedades en la app estate
class EstatePropertyOffer(models.Model):
    _name = "estate.property.offer"
    _description = "Property Offer"
    _order = "price desc"

    # Monto de la oferta
    price = fields.Float(string="Price", required=True)

    # Estado de la oferta: aceptada o rechazada
    status = fields.Selection([
        ('accepted', 'Accepted'),
        ('refused', 'Refused')
    ], string="Status", copy=False)


    # Comprador que realiza la oferta
    partner_id = fields.Many2one(
        "res.partner",
        string="Partner",
        required=True
    )

    # Propiedad relacionada con esta oferta
    property_id = fields.Many2one(
        "estate.property",
        string="Property",
        required=True,
        ondelete='cascade'
    )


    # Días de validez de la oferta
    validity = fields.Integer(string="Validity (days)", default=7)
    # Fecha límite de la oferta, calculada a partir de la validez
    date_deadline = fields.Date(
        string="Deadline",
        compute="_compute_date_deadline",
        inverse="_inverse_date_deadline",
        store=True
    )

    # Tipo de propiedad (campo relacionado)
    property_type_id = fields.Many2one(
        'estate.property.type',
        related='property_id.property_type_id',
        store=True,
        string='Property Type'
    )

    @api.depends('validity', 'create_date')
    def _compute_date_deadline(self):
        # Calcula la fecha límite en base a la validez y la fecha de creación
        for offer in self:
            start_date = offer.create_date.date() if offer.create_date else fields.Date.today()
            offer.date_deadline = start_date + timedelta(days=offer.validity)


    def _inverse_date_deadline(self):
        # Actualiza la validez si se cambia la fecha límite manualmente
        for offer in self:
            start_date = offer.create_date.date() if offer.create_date else fields.Date.today()
            offer.validity = (offer.date_deadline - start_date).days


    @api.model
    def create(self, vals):
        # Evita crear ofertas con precio menor o igual a una existente
        property_rec = self.env['estate.property'].browse(vals['property_id'])
        if property_rec.offer_ids.filtered(lambda o: o.price >= vals['price']):
            raise UserError("No se puede crear una oferta con un precio inferior o igual a otra oferta existente.")
        # Cambia el estado de la propiedad si es la primera oferta
        if property_rec.state == 'new':
            property_rec.write({'state': 'offer_received'})
        return super().create(vals)


    def action_accept(self):
        # Acepta esta oferta y actualiza la información de la propiedad
        for offer in self:
            if offer.property_id.offer_ids.filtered(lambda o: o.status == 'accepted'):
                raise UserError("Ya hay una oferta aceptada para esta propiedad.")
            offer.status = 'accepted'
            offer.property_id.selling_price = offer.price
            offer.property_id.buyer_id = offer.partner_id
            offer.property_id.write({'state': 'offer_accepted'})
            print('DEBUG action_accept: selling_price', offer.property_id.selling_price, 'buyer_id', offer.property_id.buyer_id)
        return True


    def action_refuse(self):
        # Rechaza esta oferta
        for offer in self:
            offer.status = 'refused'
        return True

    # Asegura que el precio de la oferta sea siempre positivo
    _sql_constraints = [
        ('check_price_positive',
         'CHECK(price > 0)',
         'The offer price must be strictly positive.')
    ]


    # Indicadores de ofertas aceptadas o rechazadas
    accepted_bool = fields.Boolean(
        string="Aceptada",
        compute="_compute_offer_flags",
        store=True,
        readonly=True
    )
    refused_bool = fields.Boolean(
        string="Rechazada",
        compute="_compute_offer_flags",
        store=True,
        readonly=True
    )


    @api.depends('status')
    def _compute_offer_flags(self):
        # Establece los flags booleanos según el estado de la oferta
        for offer in self:
            offer.accepted_bool = offer.status == 'accepted'
            offer.refused_bool = offer.status == 'refused'