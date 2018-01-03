$('#pleaseWaitDialog').on('show.bs.modal', function(event) {
  var button = $(event.relatedTarget) // Button that triggered the modal

  var modal = $(this)

  modal.find('.modal-title').text('Loading, please wait...')
  modal.find('.modal-result').load('/modalcmdshowcdpneigh/' + hostname)
})

$('#pleaseWaitDialog').on('hidden.bs.modal', function() {
  var modal = $(this)
  modal.find('.modal-title').text('')
  modal.find('.modal-result').text('')
})
