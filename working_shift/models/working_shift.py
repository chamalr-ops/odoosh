from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from datetime import datetime


class WorkingShift(models.Model):
    _name = 'working.shift'
    _inherit = ['mail.thread']
    _description = 'Working Shifts'

    name = fields.Char(string="Name", copy=False, tracking=True, default='New', readonly=True)
    start_date = fields.Date(string='Start Date', tracking=True, copy=False)
    end_date = fields.Date(string="End Date", tracking=True, copy=False)
    shift_lines = fields.One2many(comodel_name='working.shift.lines', inverse_name="working_shift_id",
                                  string="Shift Lines", tracking=True, copy=True)

    @api.onchange('start_date', 'end_date')
    def check_start_date_and_end_date(self):
        """"Start Date and End Date basic validation"""
        if self.start_date and self.end_date:
            if self.start_date > self.end_date:
                raise ValidationError("Start date and End date not matching")
            all_records = self.sudo().search([])
            for record in all_records:
                start_date = record.start_date
                end_date = record.end_date
                if start_date == self.start_date and end_date == self.end_date:
                    raise ValidationError("You have a record already for these days")

    @api.model
    def create(self, values):
        if 'start_date' not in values or 'end_date' not in values:
            values['name'] = "New"

        if 'start_date' in values and 'end_date' in values:
            values['name'] = "From " + str(values['start_date']) + " To " + str(values['end_date'])
        return super(WorkingShift, self).create(values)

    def write(self, values):
        if 'start_date' in values and 'end_date' in values:
            values['name'] = "From " + str(values['start_date']) + " To " + str(values['end_date'])
        return super(WorkingShift, self).write(values)


class WorkingShiftLines(models.Model):
    _name = 'working.shift.lines'

    shift_date = fields.Date(string='Shift Date', required=True)
    shift_no_one = fields.Selection([('one', 'Shift One'), ('two', 'Shift Two')], string="Shift", default='one')
    one_start = fields.Float(string='Start Time')
    one_end = fields.Float(string='End Time')
    shift_no_two = fields.Selection([('one', 'Shift One'), ('two', 'Shift Two')], string="Shift", default='two')
    two_start = fields.Float(string='Start Time')
    two_end = fields.Float(string='End Time')
    working_shift_id = fields.Many2one(comodel_name='working.shift')

    @api.onchange('shift_date')
    def _set_shift_date(self):
        if not self.shift_date:
            self.shift_date = self.working_shift_id.start_date
