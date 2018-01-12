$('#modalLocalCredentials').on('show.bs.modal', function(event) {
  var button = $(event.relatedTarget) // Button that triggered the modal

  var hostname = button.data('hostname') // Extract info from data-* attributes
  var hostid = button.data('hostid') // Extract info from data-* attributes

  var modal = $(this)

  // Check to see if host has a currently established and active SSH session.
  // If so, do not prompt user for credentials.  Show loading screen modal while loading host on existing session.
  // If not, show modal prompting user for local credentials for the specific device.
  $.ajax({
    type: 'POST',
    url: '/ajaxcheckhostactivesshsession/' + hostid,
    success: function(response) {
      if (response == 'True') {
        // SSH session already established.  Do not prompt for credentials.
        // Loading wheel in modal HTML code will load until the below URL fully loads
        url = '/db/viewhosts/' + hostid;
        window.location.href = url;
      }
      else {
        // SSH session is not established.  Prompt for credentials.
        modal.find('.modal-title').text('Local credentials for ' + hostname)
        modal.find('.modal-result').load('/modallocalcredentials/' + hostid, function() {
          // Hide loading wheel in modal, which is really only used for above 'if' statement, if SSH session is already established.
          $("#loading").hide();
          $("#loadingWheel").hide();
          $("#loadingContentHide").show();
        });
      }
    },
    error: function(response) {
      console.log(response);
      console.log('error');
    }
  });
})

$('#modalLocalCredentials').on('hidden.bs.modal', function() {
  var modal = $(this)
  modal.find('.modal-title').text('')
  modal.find('.modal-result').text('')
})