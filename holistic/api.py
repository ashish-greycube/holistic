
import datetime
import json

import frappe
from frappe import _
from frappe.core.doctype.sms_settings.sms_settings import send_sms
from frappe.model.document import Document
from frappe.model.mapper import get_mapped_doc
from frappe.utils import flt, get_link_to_form, get_time, getdate,add_days,cint,get_datetime,get_time_str,to_timedelta,get_timedelta,get_date_str,format_date,get_url_to_form
from erpnext.hr.doctype.employee.employee import is_holiday
from frappe.utils.csvutils import getlink
from frappe.model.naming import set_name_by_naming_series
from frappe.model.naming import make_autoname
from erpnext.healthcare.doctype.healthcare_settings.healthcare_settings import get_receivable_account,get_income_account
from erpnext.stock.get_item_details import get_price_list_rate_for, process_args


def after_migrations():
	update_dashboard_link_for_core_doctype(doctype='Patient Appointment',link_doctype='Patient Appointment',link_fieldname='parent_patient_appointment_cf',group='Treatment Plan')
	update_dashboard_link_for_core_doctype(doctype='Patient Appointment',link_doctype='Sales Invoice',link_fieldname='holistic_ref_patient_appointment',group='Sales Invoice')

def update_dashboard_link_for_core_doctype(doctype,link_doctype,link_fieldname,group=None):
	try:
		d = frappe.get_doc("Customize Form")
		if doctype:
			d.doc_type = doctype
		d.run_method("fetch_to_customize")
		for link in d.get('links'):
			if link.link_doctype==link_doctype and link.link_fieldname==link_fieldname:
				# found so just return
				return
		d.append('links', dict(link_doctype=link_doctype, link_fieldname=link_fieldname,table_fieldname=None,group=group))
		d.run_method("save_customization")
		frappe.clear_cache()
	except Exception:
		frappe.log_error(frappe.get_traceback())		

@frappe.whitelist()
def book_patient_appointment(date, practitioner,no_of_sessions,time,department,parent_doc):
	date = getdate(date)
	last_parent_doc=frappe.get_doc("Patient Appointment", parent_doc)
	appointment_interval= frappe.db.get_single_value('Holistic Settings', 'appointment_interval') or 1
	step_index=0
	for step in last_parent_doc.therapy_steps:
		if step.booked_treatment_appointments:
			step_index=step.idx

	if step_index>0 and last_parent_doc.therapy_steps and last_parent_doc.therapy_steps[step_index-1].booked_treatment_appointments:
		last_booked_treatment_appointment=last_parent_doc.therapy_steps[step_index-1].booked_treatment_appointments.split("\n")[-1].split(", ")[0]
		last_appointment_date=frappe.db.get_value("Patient Appointment", last_booked_treatment_appointment, 'appointment_date')
		next_date=add_days(last_appointment_date,appointment_interval)
	else:
		next_date=add_days(date,appointment_interval)
	
	schedule_duration=cint(time)
	child_doc_msg=[]
	child_doc_names=[]

	for session in range(cint(no_of_sessions)):
		appointment=get_availability_data(next_date,practitioner,schedule_duration)
		while appointment == -1:
			next_date=add_days(next_date,1)
			appointment=get_availability_data(next_date,practitioner,schedule_duration)

		if appointment != -1:
			child_doc_name=create_child_item_appointment(parent_doc,appointment,department)
			child_doc_detail=child_doc_name+', '+format_date(get_date_str(appointment['appointment_date']))+', '+get_time_str(appointment['appointment_time'])
			child_doc_msg.append(_("Treatment Plan Appointment:{0} is created".format(getlink("Patient Appointment", child_doc_name))))	
			child_doc_names.append(child_doc_detail)		
			next_date=add_days(next_date,appointment_interval)
		
	if len(child_doc_msg)>0:
		msg='<br>'.join(child_doc_msg)
		frappe.msgprint(msg, indicator="green",alert=1)		
		return '\n'.join(child_doc_names) 
	else:
		return "no appointment created"

def create_child_item_appointment(parent_doc_name,child_fields,department):
	print('-'*100)
	print('department',department)
	parent_doc=frappe.get_doc("Patient Appointment", parent_doc_name)
	child_doc={
		'doctype': 'Patient Appointment',
		'patient':parent_doc.patient,
		'patient_name':parent_doc.patient_name,
		'patient_sex':parent_doc.patient_sex,
		'patient_age':parent_doc.patient_age,
		'inpatient_record':parent_doc.inpatient_record,
		'company':parent_doc.company,
		'practitioner':child_fields['practitioner'],
		'patient_detail_annotation_cf':parent_doc.patient_detail_annotation_cf,
		'annotated_patient_detail_image_cf':parent_doc.annotated_patient_detail_image_cf,
		'tc_name':parent_doc.tc_name,
		'terms':parent_doc.terms,
		'parent_patient_appointment_cf':parent_doc.name,
		'service_unit':child_fields['service_unit'],
		'appointment_type':parent_doc.appointment_type,
		'complaint_cf':parent_doc.complaint_cf,
		'diagnosis_cf':parent_doc.diagnosis_cf,
		'appointment_date':child_fields['appointment_date'],
		'appointment_time':child_fields['appointment_time']
	}
	child=frappe.get_doc(child_doc)
	child.insert(ignore_permissions=True)
	frappe.db.set_value("Patient Appointment",child.name,'department', department)
	frappe.db.set_value("Patient Appointment",child.name,'duration', child_fields['duration'])
	return child.name

@frappe.whitelist()
def get_availability_data(date, practitioner,schedule_duration):
	"""
	Get availability data of 'practitioner' on 'date'
	:param date: Date to check in schedule
	:param practitioner: Name of the practitioner
	:return: dict containing a list of available slots, list of appointments and time of appointments
	"""

	date = getdate(date)
	weekday = date.strftime("%A")

	practitioner_doc = frappe.get_doc("Healthcare Practitioner", practitioner)

	check_employee_wise_availability(date, practitioner_doc)

	if practitioner_doc.practitioner_schedules:
		slot_details = get_available_slots(practitioner_doc, date,schedule_duration)
	else:
		frappe.throw(
			_(
				"{0} does not have a Healthcare Practitioner Schedule. Add it in Healthcare Practitioner master"
			).format(practitioner),
			title=_("Practitioner Schedule Not Found For Given Criteria"),
		)

	if not slot_details:
		# TODO: return available slots in nearby dates
		frappe.msgprint(
			_("Healthcare Practitioner not available on {0}. Moving to next day..").format(weekday), title=_("Not Available"),alert=1
		)
		return -1

	return slot_details

def check_employee_wise_availability(date, practitioner_doc):
	employee = None
	if practitioner_doc.employee:
		employee = practitioner_doc.employee
	elif practitioner_doc.user_id:
		employee = frappe.db.get_value("Employee", {"user_id": practitioner_doc.user_id}, "name")

	if employee:
		# check holiday
		if is_holiday(employee, date):
			frappe.msgprint(_("{0} is a holiday. Moving to next day..".format(date)), title=_("Not Available"),alert=1)
			return -1

		# check leave status
		leave_record = frappe.db.sql(
			"""select half_day from `tabLeave Application`
			where employee = %s and %s between from_date and to_date
			and docstatus = 1""",
			(employee, date),
			as_dict=True,
		)
		if leave_record:
			if leave_record[0].half_day:
				frappe.msgprint(
					_("{0} is on a Half day Leave on {1}. Moving to next day..").format(practitioner_doc.name, date),
					title=_("Not Available"),alert=1
				)
				return -1
			else:
				frappe.msgprint(
					_("{0} is on Leave on {1}. Moving to next day..").format(practitioner_doc.name, date), title=_("Not Available"),alert=1
				)
				return -1

def get_available_slots(practitioner_doc, date,schedule_duration):
	available_slots = slot_details = []
	child_slot={}
	weekday = date.strftime("%A")
	practitioner = practitioner_doc.name
	schedule_with_required_duration_found=False
	for schedule_entry in practitioner_doc.practitioner_schedules:

		validate_practitioner_schedules(schedule_entry, practitioner)
		practitioner_schedule = frappe.get_doc("Practitioner Schedule", schedule_entry.schedule)

		if practitioner_schedule and not practitioner_schedule.disabled and practitioner_schedule.duration_cf == schedule_duration and schedule_with_required_duration_found==False:
			schedule_with_required_duration_found=True
			available_slots = []
			for time_slot in practitioner_schedule.time_slots:
				if weekday == time_slot.day:
					available_slots.append(get_time_str(time_slot.from_time))

			if available_slots:
				appointments = []
				# overlap changes
				allow_overlap = 1
				service_unit_capacity = 0
				# fetch all appointments to practitioner by service unit
				filters = {
					"practitioner": practitioner,
					"service_unit": schedule_entry.service_unit,
					"appointment_date": date,
					"status": ["not in", ["Cancelled"]],
				}

				if schedule_entry.service_unit:
					slot_name = f"{schedule_entry.schedule}"
					allow_overlap, service_unit_capacity = frappe.get_value(
						"Healthcare Service Unit",
						schedule_entry.service_unit,
						["overlap_appointments", "service_unit_capacity"],
					)
					# overlap changes
					allow_overlap=1
					if not allow_overlap:
						# fetch all appointments to service unit
						filters.pop("practitioner")
				else:
					slot_name = schedule_entry.schedule
					# fetch all appointments to practitioner without service unit
					filters["practitioner"] = practitioner
					filters.pop("service_unit")

				appointments = frappe.get_all(
					"Patient Appointment",
					filters=filters,
					fields=["name", "appointment_time", "duration", "status"],
				)

				# remove slots with appointments
				booked_slots=[]
				for appointment in appointments:
					booked_slots.append(get_time_str(appointment.appointment_time))

				if len(booked_slots)>0:
						available_slots=list(filter(lambda slots: slots not in booked_slots,available_slots))

				if len(available_slots)<1:
					return -1
				# slot_details.append(
				# 	{
				# 		"slot_name": slot_name,
				# 		"appointment_date":date,
				# 		"service_unit": schedule_entry.service_unit,
				# 		"avail_slot": available_slots[0],
				# 		"appointments": appointments,
				# 		"allow_overlap": allow_overlap,
				# 		"service_unit_capacity": service_unit_capacity,
				# 		"practitioner_name": practitioner_doc.practitioner_name,
				# 	}
					
				# )

				child_slot={
					"appointment_time":available_slots[0],
					"duration":schedule_duration,
					"practitioner":practitioner_doc.practitioner_name,
					"appointment_date":date,
					"service_unit":schedule_entry.service_unit
				}
	if schedule_with_required_duration_found==False:
		frappe.throw(
			_(
				"Practitioner {0} does not have a Practitioner Schedule  with duration {1}."
			).format(
				get_link_to_form("Healthcare Practitioner", practitioner_doc.practitioner_name),
				frappe.bold(schedule_duration),
			),
			title=_("Schedule with required duration Not Found"),
		)		
	return child_slot

def validate_practitioner_schedules(schedule_entry, practitioner):
	if schedule_entry.schedule:
		if not schedule_entry.service_unit:
			frappe.throw(
				_(
					"Practitioner {0} does not have a Service Unit set against the Practitioner Schedule {1}."
				).format(
					get_link_to_form("Healthcare Practitioner", practitioner),
					frappe.bold(schedule_entry.schedule),
				),
				title=_("Service Unit Not Found"),
			)

	else:
		frappe.throw(
			_("Practitioner {0} does not have a Practitioner Schedule assigned.").format(
				get_link_to_form("Healthcare Practitioner", practitioner)
			),
			title=_("Practitioner Schedule Not Found"),
		)


def get_appointment_item(department,patient,practitioner,company,qty,name, item):
	item_code=frappe.db.get_value('Medical Department',department, 'item_cf')
	if not item_code:
		frappe.throw(
			_("Medical Department {0} does not have item assigned.").format(
				get_link_to_form('Medical Department',department)
			),
			title=_("Item is not Defined."),
		)		
	args = {
		"price_list": frappe.db.get_single_value('Selling Settings', 'selling_price_list'),
		"customer":  frappe.get_value("Patient", patient, "customer"),
		"qty": qty,
	}

	price = get_price_list_rate_for(process_args(args), item_code)		
	item.item_code = item_code
	item.description = _("Consulting Charges: {0}").format(practitioner)
	item.income_account = get_income_account(practitioner, company)
	item.cost_center = frappe.get_cached_value("Company",company, "cost_center")
	item.rate = price
	item.amount = price*qty
	item.qty = qty
	# item.reference_dt = "Patient Appointment"
	item.holistic_ref_patient_appointment_item = name
	return item

@frappe.whitelist()
def create_sales_invoice(appointment_doc):
	appointment_doc=frappe.get_doc("Patient Appointment", appointment_doc)
	if appointment_doc.parent_patient_appointment_cf:
		frappe.throw(
			_("Sales Invoice cannot be created for Treatment Appointment.(Child). Please use {0}.").format(
				get_link_to_form('Patient Appointment',appointment_doc.parent_patient_appointment_cf)
			),
			title=_("Treatment Appointment.(Child) Error."),
		)		
	sales_invoice = frappe.new_doc("Sales Invoice")
	sales_invoice.patient = appointment_doc.patient
	sales_invoice.holistic_ref_patient_appointment=appointment_doc.name
	sales_invoice.customer = frappe.get_value("Patient", appointment_doc.patient, "customer")
	sales_invoice.appointment = appointment_doc.name
	sales_invoice.due_date = getdate()
	sales_invoice.company = appointment_doc.company
	sales_invoice.debit_to = get_receivable_account(appointment_doc.company)

	if not appointment_doc.parent_patient_appointment_cf and len(appointment_doc.therapy_steps)>0:
		for therapy_item in appointment_doc.therapy_steps:
			previous_qty=0
			previous_qty_data=frappe.db.get_list('Sales Invoice Item', filters={'holistic_ref_patient_appointment_item': therapy_item.name,'docstatus':1},fields=['qty'],pluck='qty')
			if len(previous_qty_data)>0:
				for prev_qty in previous_qty_data:
					previous_qty=prev_qty+previous_qty
			print('previous_qty',previous_qty)	
			actual_qty=flt(therapy_item.no_of_sessions-previous_qty)
			if actual_qty>0:
				item = sales_invoice.append("items", {})
				item = get_appointment_item(department=therapy_item.department,patient=appointment_doc.patient,
									practitioner=therapy_item.healthcare_practitioner_follow_up,company=appointment_doc.company,qty=actual_qty,name=therapy_item.name,item=item)
	print(sales_invoice.get('items'),"sales_invoice.get('items')")
	if len(sales_invoice.get('items'))==0:
		frappe.throw(
			_("Sales Invoice cannot be created as there are no pending items"),
			title=_("No eligible Item."),
		)		

	

	# Add payments if payment details are supplied else proceed to create invoice as Unpaid
	if appointment_doc.mode_of_payment and appointment_doc.paid_amount:
		sales_invoice.is_pos = 1
		payment = sales_invoice.append("payments", {})
		payment.mode_of_payment = appointment_doc.mode_of_payment
		payment.amount = appointment_doc.paid_amount

	sales_invoice.set_missing_values(for_validate=True)
	sales_invoice.run_method('set_missing_values')
	sales_invoice.run_method('calculate_taxes_and_total')
	# sales_invoice.flags.ignore_mandatory = True
	sales_invoice.save(ignore_permissions=True)
	# sales_invoice.submit()
	frappe.msgprint(_("Sales Invoice {0} created").format(get_link_to_form('Sales Invoice',sales_invoice.name)), alert=True)
	if appointment_doc.holistic_ref_sales_invoices:
		holistic_ref_sales_invoices=appointment_doc.holistic_ref_sales_invoices+'\n'+sales_invoice.name
	else:
		holistic_ref_sales_invoices=sales_invoice.name
	frappe.db.set_value(
		"Patient Appointment",
		appointment_doc.name,
		{"holistic_ref_sales_invoices": holistic_ref_sales_invoices},
	)	
	return 	get_url_to_form('Sales Invoice',sales_invoice.name)


def remove_si_reference_from_patient_appointment(self,method):
	print('-'*100)
	patient_appointment=frappe.db.get_all('Patient Appointment', filters={'holistic_ref_sales_invoices': self.name})
	if len(patient_appointment)>0:
		frappe.db.set_value("Patient Appointment",patient_appointment[0].name,{"holistic_ref_sales_invoices": None},)			
		frappe.msgprint(_("Sales Invoice reference is removed from  Patient Appointment {0}").format(get_link_to_form('Patient Appointment',patient_appointment[0].name)), alert=True)