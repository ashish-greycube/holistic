/*
(c) ESS 2015-16
*/
frappe.listview_settings['Patient Appointment'] = {
	total_fields:10,
	hide_name_column: true ,
	// filters: [["status", "=", "Open"]],
    add_fields: ["patient","practitioner","appointment_date","appointment_time","parent_patient_appointment_cf"],
	get_indicator: function(doc) {
		// var colors = {
		// 	"Open": "orange",
		// 	"Scheduled": "yellow",
		// 	"Closed": "green",
		// 	"Cancelled": "red",
		// 	"Expired": "grey"
		// };
        if (doc.parent_patient_appointment_cf== undefined){
            return [__(doc.status), "blue", "status,=," + doc.status];
        }else{
            return [__(doc.status), "green", "status,=," + doc.status];
        }
	},
	// onload: function(listview) {
	// 	listview.page.add_menu_item(__("XX"), function() {
	// 		let url = `/api/method/holistic.holistic.print_format.patient_appointment_list.__init__.get_appointment_list_details`,
	// 		args = {
	// 		  docnames: cur_list.get_checked_items(),
	// 		};
	// 	  open_url_post(url, args, true);			
	// 	});
	// }	
};
