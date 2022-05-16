var sourceImage ;
var targetRoot;
var maState;

frappe.ui.form.on("Patient Appointment", {
  refresh: function(frm) {
    if (frm.doc.__islocal == undefined && frm.doc.ref_sales_invoice == undefined ) {
      frm.add_custom_button('Sales Invoice', () => {
        frappe.call('holistic.api.create_sales_invoice', {
          appointment_doc: frm.doc.name
      }).then(r => {
          console.log(r.message)
      })
    }, 'Create');    
    }    
    frm.set_query('appointment_type', function() {
			return {
				filters: { 'default_duration': 0 }
			};
		});   
  //   frm.set_query('healthcare_practitioner_follow_up', 'therapy_steps', (doc, cdt, cdn) => {
  //     var row = locals[cdt][cdn];
  //     return {
  //         filters: {
  //           department: row.department
  //         }
  //     }
  // })    
  if (frm.doc.__islocal == undefined ) {
    let intro = frm.doc.parent_patient_appointment_cf?
    __("<b>Treatment Appointment.(Child)</b>") : __("<b>Main Appointment.</b>");
    let color = frm.doc.parent_patient_appointment_cf?
      "orange":"green"
      frm.set_intro(intro,color)
 } 
  },
	onload_post_render: function(frm) {
    $(frm.fields_dict['patient_detail_html_cf'].wrapper)
    .html('<div  style="position: relative; display: flex;flex-direction: column;align-items: center;justify-content: center;padding-top: 50px;"> \
    <img  id="sourceImage"   src="/assets/holistic/image/humanbody.png" style="max-width: 900px; max-height: 80%;"  crossorigin="anonymous" /> \
    <img  id="sampleImage"   src="/assets/holistic/image/humanbody.png"  style="max-width: 900px; max-height: 100%; position: absolute;" crossorigin="anonymous" /> \
    </div>');

    setSourceImage(document.getElementById("sourceImage"));

    const sampleImage = document.getElementById("sampleImage");
    sampleImage.addEventListener("click", () => {
      showMarkerArea(sampleImage);
    });      
  }
})

function setSourceImage(source) {
  sourceImage = source;
  targetRoot = source.parentElement;
}

function showMarkerArea(target) {
  const markerArea = new markerjs2.MarkerArea(sourceImage);
    markerArea.renderImageQuality = 0.5;
    markerArea.renderImageType = 'image/jpeg';

  // since the container div is set to position: relative it is now our positioning root
  // end we have to let marker.js know that
  markerArea.targetRoot = targetRoot;
  markerArea.addRenderEventListener((imgURL, state) => {
    target.src = imgURL;
    // save the state of MarkerArea
    cur_frm.doc.patient_detail_annotation_cf=JSON.stringify(state)
   
    cur_frm.set_value('annotated_patient_detail_image_cf', imgURL)
    cur_frm.save()
  });
  markerArea.show();
  // if previous state is present - restore it
  if (cur_frm.doc.patient_detail_annotation_cf) {
    markerArea.restoreState(JSON.parse(cur_frm.doc.patient_detail_annotation_cf));
  }
}


frappe.ui.form.on("Therapy plan in appointment",{
  book_appointment:function(frm,cdt,cdn) {
    if (frm.is_dirty()==true) {
      frappe.msgprint(__('Please save the form first.'));
    } else {
      let row=locals[cdt][cdn]
    frappe.call({
      method: 'holistic.api.book_patient_appointment',
      args: {
        department:row.department,
        practitioner:row.healthcare_practitioner_follow_up,
        date: frm.doc.appointment_date,
        no_of_sessions: row.no_of_sessions,
        time:row.time,
        parent_doc:frm.doc.name    
      },
      callback: (r) => {
        console.log('r',r)
        let data = r.message;
        if (row.booked_treatment_appointments) {
          frappe.model.set_value(cdt, cdn, 'booked_treatment_appointments',row.booked_treatment_appointments+"\n"+data);
        } else {
          frappe.model.set_value(cdt, cdn, 'booked_treatment_appointments',data);
        }
        frm.refresh_field("therapy_steps");
        // frm.enable_save();
				frm.save();
      }
    })      
    }
  
  }
})