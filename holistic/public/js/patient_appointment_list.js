/*
(c) ESS 2015-16
*/
frappe.listview_settings['Patient Appointment'] = {
	// filters: [["status", "=", "Open"]],
    add_fields: ["parent_patient_appointment_cf"],
	get_indicator: function(doc) {
		// var colors = {
		// 	"Open": "orange",
		// 	"Scheduled": "yellow",
		// 	"Closed": "green",
		// 	"Cancelled": "red",
		// 	"Expired": "grey"
		// };
        console.log('doc.parent_patient_appointment_cf',doc.parent_patient_appointment_cf)
        if (doc.parent_patient_appointment_cf== undefined){
            return [__(doc.status), "green", "status,=," + doc.status];
        }else{
            return [__(doc.status), "yellow", "status,=," + doc.status];
        }
		// return [__(doc.status), colors[doc.status], "status,=," + doc.status];
	}
};
