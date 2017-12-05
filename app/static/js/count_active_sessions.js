// Gets count of currently active SSH sessions
$(document).ready(function(){
	//var loc = location.href.substr(location.href.lastIndexOf('/') + 1);
	$.ajax({
		url: '/getsshsessionscount',
		success: function(data) {
			//var result = JSON.stringify(data); // Convert jsonify'd data from python
			//result = result.replace(/\"/g, "") // Remove double quotes from string
			var count = document.getElementById('activeSSHSessionCount'); // Get DIV element from HTML page
			//count.innerHTML = result; // Pass string to DIV on HTML page
			count.innerHTML = data
	   }
	});
});