from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.utils.print_format import download_pdf
from frappe.utils import getdate,cstr

@frappe.whitelist()
def get_appointment_list_details(docname):
    arabic_days={"Sunday":"الاحد","Monday":"الاثنين","Tuesday":"الثلاثاء","Wednesday":"الأربعاء","Thursday":"الخميس","Friday":"الجمعه","Saturday":"السبت"}
    doc=frappe.get_doc("Patient Appointment",docname)
    day=getdate(doc.appointment_date).strftime("%A")
    patient_age = cstr(frappe.get_doc("Patient",doc.patient).get_age())
    doc.patient_age_str=patient_age

    child_appointments=frappe.db.get_list('Patient Appointment',filters={'parent_patient_appointment_cf':docname},
    fields=['appointment_time','appointment_date','service_unit'],order_by='appointment_date, appointment_time desc',)
    all_appointments=[]
    all_appointments.append({'appointment_date':doc.appointment_date,'appointment_time':doc.appointment_time,
    'service_unit':doc.service_unit,
    'day':day+'<br>'+arabic_days.get(day)   
    })
    if len(child_appointments)>0:
        for child in child_appointments:
            day=getdate(child.appointment_date).strftime("%A")
            child['day']=day+'<br>'+arabic_days.get(day)
            all_appointments.append(child)
    doc.all_appointments=all_appointments
    download_pdf(doctype=doc.doctype, name=docname, format="patient_appointment_list", doc=doc)