from . import __version__ as app_version

app_name = "holistic"
app_title = "Holistic"
app_publisher = "GreyCube Technologies"
app_description = "Customization for patient booking"
app_icon = "octicon octicon-pencil"
app_color = "blue"
app_email = "admin@greycube.in"
app_license = "MIT"

# Includes in <head>
# ------------------

# include js, css files in header of desk.html
# app_include_css = "/assets/holistic/css/holistic.css"
# app_include_js = "/assets/holistic/js/holistic.js"
app_include_js =  ["/assets/holistic/js/markerjs2.js"]
# include js, css files in header of web template
# web_include_css = "/assets/holistic/css/holistic.css"
# web_include_js = "/assets/holistic/js/holistic.js"

# include custom scss in every website theme (without file extension ".scss")
# website_theme_scss = "holistic/public/scss/website"

# include js, css files in header of web form
# webform_include_js = {"doctype": "public/js/doctype.js"}
# webform_include_css = {"doctype": "public/css/doctype.css"}

# include js in page
# page_js = {"page" : "public/js/file.js"}

# include js in doctype views
doctype_js = {"Patient Appointment" : "public/js/patient_appointment.js"}
doctype_list_js = {"Patient Appointment" : "public/js/patient_appointment_list.js"}
# doctype_tree_js = {"doctype" : "public/js/doctype_tree.js"}
doctype_calendar_js = {"Patient Appointment" : "public/js/patient_appointment_calendar.js"}

# Home Pages
# ----------

# application home page (will override Website Settings)
# home_page = "login"

# website user home page (by Role)
# role_home_page = {
#	"Role": "home_page"
# }

# Generators
# ----------

# automatically create page for each record of this doctype
# website_generators = ["Web Page"]

# Installation
# ------------

# before_install = "holistic.install.before_install"
# after_install = "holistic.install.after_install"

# Uninstallation
# ------------

# before_uninstall = "holistic.uninstall.before_uninstall"
# after_uninstall = "holistic.uninstall.after_uninstall"
after_migrate = "holistic.api.after_migrations"
# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config

# notification_config = "holistic.notifications.get_notification_config"

# Permissions
# -----------
# Permissions evaluated in scripted ways

# permission_query_conditions = {
# 	"Event": "frappe.desk.doctype.event.event.get_permission_query_conditions",
# }
#
# has_permission = {
# 	"Event": "frappe.desk.doctype.event.event.has_permission",
# }

# DocType Class
# ---------------
# Override standard doctype classes

# override_doctype_class = {
# 	"ToDo": "custom_app.overrides.CustomToDo"
# }

# Document Events
# ---------------
# Hook on document methods and events

doc_events = {
	"Patient Appointment":{
		"validate":"holistic.api.stop_save_for_closed_status"
	},
	"Sales Invoice": {
		"before_cancel": "holistic.api.remove_si_reference_from_patient_appointment",
	}
}

# Scheduled Tasks
# ---------------

# scheduler_events = {
# 	"all": [
# 		"holistic.tasks.all"
# 	],
# 	"daily": [
# 		"holistic.tasks.daily"
# 	],
# 	"hourly": [
# 		"holistic.tasks.hourly"
# 	],
# 	"weekly": [
# 		"holistic.tasks.weekly"
# 	]
# 	"monthly": [
# 		"holistic.tasks.monthly"
# 	]
# }

# Testing
# -------

# before_tests = "holistic.install.before_tests"

# Overriding Methods
# ------------------------------
#
# override_whitelisted_methods = {
# 	"frappe.desk.doctype.event.event.get_events": "holistic.event.get_events"
# }
#
# each overriding function accepts a `data` argument;
# generated from the base implementation of the doctype dashboard,
# along with any modifications made in other Frappe apps
# override_doctype_dashboards = {
# 	"Task": "holistic.task.get_dashboard_data"
# }

# exempt linked doctypes from being automatically cancelled
#
# auto_cancel_exempted_doctypes = ["Auto Repeat"]


# User Data Protection
# --------------------

user_data_fields = [
	{
		"doctype": "{doctype_1}",
		"filter_by": "{filter_by}",
		"redact_fields": ["{field_1}", "{field_2}"],
		"partial": 1,
	},
	{
		"doctype": "{doctype_2}",
		"filter_by": "{filter_by}",
		"partial": 1,
	},
	{
		"doctype": "{doctype_3}",
		"strict": False,
	},
	{
		"doctype": "{doctype_4}"
	}
]

# Authentication and authorization
# --------------------------------

# auth_hooks = [
# 	"holistic.auth.validate"
# ]

# Translation
# --------------------------------

# Make link fields search translated document names for these DocTypes
# Recommended only for DocTypes which have limited documents with untranslated names
# For example: Role, Gender, etc.
# translated_search_doctypes = []
