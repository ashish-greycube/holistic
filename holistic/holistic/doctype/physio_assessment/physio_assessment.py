# Copyright (c) 2022, GreyCube Technologies and contributors
# For license information, please see license.txt

import json

import frappe
from frappe import _, throw
from frappe.model.document import Document
from frappe.utils import cint
from frappe.utils.jinja import validate_template
from six import string_types


class PhysioAssessment(Document):
	def validate(self):
		if self.terms:
			validate_template(self.terms)


@frappe.whitelist()
def get_terms_and_conditions(template_name, doc):
	if isinstance(doc, string_types):
		doc = json.loads(doc)

	terms_and_conditions = frappe.get_doc("Physio Assessment", template_name)

	if terms_and_conditions.terms:
		return frappe.render_template(terms_and_conditions.terms, doc)
