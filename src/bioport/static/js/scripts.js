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
        jQuery('#geboorteplaats_field input').autocomplete({lookup:data.geboorte});
        jQuery('#sterfplaats_field input').autocomplete({lookup:data.sterf});
    }
    var places_url = jQuery("link[rel='places_url']").attr('href');
    jQuery.getJSON(places_url, enable_comboboxes);
}

jQuery(function() {
    jQuery('#Index .credits a').click(function() {
        window.open(this.href);
        return false;
    });
}
);
