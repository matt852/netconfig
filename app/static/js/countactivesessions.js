$(document).ready(function() {
  // Gets names and provides links to devices with currently active SSH sessions
  $("#activeDevices").load("/displayactivedevicenames", function() {
    // Hide non-linking placeholder once the content fully loads
    $("#activeDevicePlaceholder").hide();
  });
  // Not sure if this is still used
  var loc = location.href.substr(location.href.lastIndexOf('/') + 1);
  $.ajax({
    url: '/getsshsessionscount',
    success: function(data) {
      // Gets count of currently active SSH sessions
      var count = document.getElementById('activeSSHSessionCount'); // Get DIV element from HTML page
      count.innerHTML = data.count;
    }
  });
});
