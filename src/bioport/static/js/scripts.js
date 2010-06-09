$.fn.clearForm = function() {
  return this.each(function() {
	 var type = this.type, tag = this.tagName.toLowerCase();
	 if (tag == 'form')
		   return $(':input',this).clearForm();
	 if (type == 'text' || type == 'password' || tag == 'textarea')
	   this.value = '';
	 else if (type == 'checkbox' || type == 'radio')
	   this.checked = false;
	 else if (tag == 'select')
	   this.selectedIndex = -1;
  });
};

var initialize_zoek_form = function() {
    var enable_comboboxes = function(data) {
        var geboorte_name = jQuery('#geboorteplaats_field input').attr('name');
        var sterf_name = jQuery('#sterfplaats_field input').attr('name');
        var geboorte_value = jQuery('#geboorteplaats_field input').attr('value');
        var sterf_value = jQuery('#sterfplaats_field input').attr('value');
        jQuery('#geboorteplaats_field input').detach();
        jQuery('#sterfplaats_field input').detach();
        jQuery('#geboorteplaats_field').createAppend('div', {id: 'geboorteplaats_combo'});
        jQuery('#sterfplaats_field').createAppend('div', {id: 'sterfplaats_combo'});
        var geboorte_combo = jQuery('#geboorteplaats_combo').ddcombo(
            {minchars:1, options: data.geboorte, title: 'Geboorte plaats'});
        var sterf_combo = jQuery('#sterfplaats_combo').ddcombo(
            {minchars:1, options: data.sterf, title: 'Sterf plaats'});
        var geboorte_input = geboorte_combo.find('input');
        var sterf_input = sterf_combo.find('input');
        if (geboorte_value) {
            geboorte_input.attr('value', geboorte_value);
        }
        if (sterf_value) {
            geboorte_input.attr('value', sterf_value);
        }

        // Bind comboBoxes to respective (now hidden) input fields.
        sterf_combo.find('input').attr('name', sterf_name);
        geboorte_combo.find('input').attr('name', geboorte_name);
        // Ensure we don't submit the UI-related helper string
        var delete_empty_field_helpers = function() {
            var geboorte_val = geboorte_input.attr('value');
            var geboorte_title = geboorte_input.attr('title');
            if (geboorte_val === geboorte_title) {
                geboorte_input.attr('value', '');
            }
            var sterf_val = sterf_input.attr('value');
            var sterf_title = sterf_input.attr('title');
            if (sterf_val === sterf_title) {
                sterf_input.attr('value', '');
            }
        };
        sterf_combo.parents('form').submit(delete_empty_field_helpers);
        
    }
    var places_url = jQuery("link[rel='places_url']").attr('href');
    jQuery.getJSON(places_url, enable_comboboxes);
}
