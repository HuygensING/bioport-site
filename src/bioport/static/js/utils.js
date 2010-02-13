
function httpReq(addr) {  
	var r = $.ajax({  
		type: 'GET',  
		url: addr,  
		async: false  
	}).responseText;  
	return r;  
}  

function refreshElem(id,aUrl) {  
	$('#'+id).hide().html(httpReq(aUrl)).fadeIn('slow');
}


