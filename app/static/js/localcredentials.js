$('#modalLocalCredentials').on('show.bs.modal', function(event) {
  var button = $(event.relatedTarget) // Button that triggered the modal

  var hostname = button.data('hostname') // Extract info from data-* attributes
  var hostid = button.data('hostid') // Extract info from data-* attributes

  var modal = $(this)

  $.ajax({
    type: 'POST',
    url: '/ajaxcheckhostactivesshsession/' + hostid,
    success: function(response) {
      console.log(response);
      console.log('success');
      if (response == 'True') {
        // SSH session already established.  Do not prompt for credentials.
        url = '/db/viewhosts/' + hostid;
        window.location.href = url;
      }
      else {
        // SSH session is not established.  Prompt for credentials.
        modal.find('.modal-title').text('Local credentials for ' + hostname)
        modal.find('.modal-result').load('/modallocalcredentials/' + hostid)
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